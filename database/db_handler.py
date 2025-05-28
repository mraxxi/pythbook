# database/db_handler.py
"""
SQLAlchemy ORM session management and CRUD operations for invoices.
Handles thread-safety concerns by ensuring sessions are created per operation or per thread.
"""
from typing import Optional, List

from sqlalchemy import create_engine, func, Integer
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession  # Alias to avoid confusion
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime, date as PythonDate
from decimal import Decimal  # For Numeric type handling
import logging
import os

from .models import Base, InvoiceDB, LineItemDB  # SQLAlchemy ORM models
from models import Invoice as BusinessInvoice, LineItem as BusinessLineItem  # Business logic models
from config.config_manager import load_config
from config.constants import SQLITE_DB_NAME

logger = logging.getLogger(__name__)
db_config_data = load_config()

# --- Engine Initialization ---
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..'))  # Assuming db_handler.py is in project_root/database/
SQLITE_DB_PATH = os.path.join(project_root, db_config_data.get('sqlite_db_name', SQLITE_DB_NAME))
sqlite_engine = create_engine(f'sqlite:///{SQLITE_DB_PATH}')
logger.info(f"SQLite engine configured for: {SQLITE_DB_PATH}")

pg_details = db_config_data.get('postgres', {})
POSTGRES_URL = None
postgres_engine = None


def get_postgres_url_from_config() -> Optional[str]:
    pg_conf = load_config().get('postgres', {})  # Reload fresh config
    if pg_conf.get('user') and pg_conf.get('host') and pg_conf.get('database'):
        # Password can be empty for some auth methods, but user, host, db usually not.
        return f"postgresql://{pg_conf['user']}:{pg_conf.get('password', '')}@{pg_conf['host']}:{pg_conf.get('port', 5432)}/{pg_conf['database']}"
    return None


def initialize_engines() -> None:
    """Initializes SQLite and PostgreSQL engines and creates tables."""
    global postgres_engine, POSTGRES_URL
    try:
        Base.metadata.create_all(sqlite_engine)
        logger.info("SQLite tables created/verified.")
    except Exception as e:
        logger.error(f"Failed to create/verify SQLite tables: {e}", exc_info=True)

    POSTGRES_URL = get_postgres_url_from_config()
    if POSTGRES_URL:
        try:
            postgres_engine = create_engine(POSTGRES_URL,
                                            pool_pre_ping=True)  # pool_pre_ping helps with stale connections
            Base.metadata.create_all(postgres_engine)
            logger.info("PostgreSQL engine initialized and tables created/verified.")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL engine or create tables: {e}", exc_info=True)
            postgres_engine = None  # Ensure it's None if initialization fails
    else:
        logger.warning("PostgreSQL URL not configured. PostgreSQL functionality will be unavailable.")


initialize_engines()  # Initialize when module is loaded

# --- Session Management ---
# For a GUI app, long DB operations should be in QThreads. Each thread gets its own session.
# For short ops directly from GUI thread, create session per operation.
_SQLiteSessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)
_PostgreSQLSessionFactory = None
if postgres_engine:
    _PostgreSQLSessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)


def get_sqlite_session() -> SQLAlchemySession:
    """Provides a new SQLAlchemy session for SQLite."""
    return _SQLiteSessionFactory()


def get_postgres_session() -> Optional[SQLAlchemySession]:
    """Provides a new SQLAlchemy session for PostgreSQL if configured."""
    if not _PostgreSQLSessionFactory:
        logger.warning("PostgreSQL is not configured or engine failed to initialize.")
        # Optionally, try to re-initialize:
        # initialize_engines()
        # if _PostgreSQLSessionFactory: return _PostgreSQLSessionFactory()
        return None
    return _PostgreSQLSessionFactory()


# --- Data Mapping Helper ---
def _map_business_invoice_to_db(business_invoice: BusinessInvoice) -> InvoiceDB:
    """Maps a business layer Invoice to a database InvoiceDB ORM model."""
    try:
        invoice_date_obj = datetime.strptime(business_invoice.invoice_date, "%Y-%m-%d").date()
    except ValueError:
        logger.error(
            f"Invalid date format for invoice {business_invoice.invoice_number}. Using current date as fallback.")
        invoice_date_obj = PythonDate.today()

    db_invoice = InvoiceDB(
        invoice_number=business_invoice.invoice_number,
        invoice_date=invoice_date_obj,
        customer_name=business_invoice.customer_name,
        customer_address=business_invoice.customer_address
        # is_synced will be set by the calling function
    )
    for biz_item in business_invoice.line_items:
        db_item = LineItemDB(
            description=biz_item.description,
            quantity=Decimal(str(biz_item.quantity)),  # Convert to Decimal
            unit_price=Decimal(str(biz_item.price))  # Convert to Decimal
        )
        db_invoice.line_items.append(db_item)
    return db_invoice


# --- CRUD Operations ---
def save_invoice_to_db(db_session: SQLAlchemySession, business_invoice: BusinessInvoice, is_synced_flag: bool) -> tuple[
    Optional[InvoiceDB], Optional[str]]:
    """
    Saves a business invoice to the specified database session.
    Returns (InvoiceDB instance or None, error message or None).
    """
    db_invoice = _map_business_invoice_to_db(business_invoice)
    db_invoice.is_synced = is_synced_flag

    # Check for existing invoice_number to prevent duplicates
    existing_invoice = db_session.query(InvoiceDB).filter(InvoiceDB.invoice_number == db_invoice.invoice_number).first()
    if existing_invoice:
        # This logic assumes invoice_number is globally unique.
        # If updating, you'd modify 'existing_invoice' instead of adding a new one.
        # For now, we treat it as an error if it exists (except for SQLite marking synced)
        if db_session.bind == postgres_engine or (
                db_session.bind == sqlite_engine and not is_synced_flag):  # If trying to add new to PG or new to SQLite
            return None, f"Invoice number '{db_invoice.invoice_number}' already exists."

    try:
        db_session.add(db_invoice)
        db_session.commit()
        db_session.refresh(db_invoice)  # To get ID and other generated fields
        logger.info(
            f"Invoice '{db_invoice.invoice_number}' saved to {db_session.bind.dialect.name}, ID: {db_invoice.id}")
        return db_invoice, None
    except IntegrityError as e:  # Specifically for unique constraint violations etc.
        db_session.rollback()
        logger.error(
            f"Integrity error saving invoice '{db_invoice.invoice_number}' to {db_session.bind.dialect.name}: {e}",
            exc_info=True)
        if "UNIQUE constraint failed: invoices_master.invoice_number" in str(e) or \
                "duplicate key value violates unique constraint" in str(
            e).lower() and "invoices_master_invoice_number_key" in str(e).lower():  # Adapt based on exact DB error
            return None, f"Invoice number '{db_invoice.invoice_number}' already exists."
        return None, f"Database integrity error: {e}"
    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error(
            f"SQLAlchemy error saving invoice '{db_invoice.invoice_number}' to {db_session.bind.dialect.name}: {e}",
            exc_info=True)
        return None, f"Database error: {e}"


def add_invoice_local(business_invoice: BusinessInvoice) -> tuple[Optional[InvoiceDB], Optional[str]]:
    """Saves an invoice to the local SQLite database, marked as unsynced."""
    session = get_sqlite_session()
    try:
        return save_invoice_to_db(session, business_invoice, is_synced_flag=False)
    finally:
        session.close()


def add_invoice_postgres(business_invoice: BusinessInvoice) -> tuple[Optional[InvoiceDB], Optional[str]]:
    """Saves an invoice to the PostgreSQL database, marked as synced."""
    session = get_postgres_session()
    if not session:
        return None, "PostgreSQL connection not available."
    try:
        # When saving directly to Postgres, it is inherently "synced" from master DB perspective.
        # The is_synced flag on InvoiceDB for Postgres records might be redundant unless
        # you have a bi-directional sync or other complex scenarios.
        return save_invoice_to_db(session, business_invoice, is_synced_flag=True)
    finally:
        if session:
            session.close()


def get_unsynced_invoices_from_local() -> List[InvoiceDB]:
    """Retrieves all unsynced invoices from the local SQLite database."""
    session = get_sqlite_session()
    try:
        invoices = session.query(InvoiceDB).filter(InvoiceDB.is_synced == False).all()
        logger.info(f"Found {len(invoices)} unsynced invoices locally.")
        return invoices
    except SQLAlchemyError as e:
        logger.error(f"Error fetching unsynced invoices: {e}", exc_info=True)
        return []
    finally:
        session.close()


def mark_local_invoice_as_synced(local_invoice_id: int) -> bool:
    """Marks a specific invoice in the local SQLite database as synced."""
    session = get_sqlite_session()
    try:
        invoice = session.query(InvoiceDB).filter(InvoiceDB.id == local_invoice_id).first()
        if invoice:
            invoice.is_synced = True
            session.commit()
            logger.info(f"Local invoice ID {local_invoice_id} marked as synced.")
            return True
        logger.warning(f"Could not find local invoice ID {local_invoice_id} to mark as synced.")
        return False
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error marking local invoice ID {local_invoice_id} as synced: {e}", exc_info=True)
        return False
    finally:
        session.close()


def transfer_local_invoice_to_postgres(pg_session: SQLAlchemySession, local_invoice_db: InvoiceDB) -> tuple[
    Optional[InvoiceDB], Optional[str]]:
    """
    Transfers a single InvoiceDB object (from local SQLite) to PostgreSQL.
    Assumes pg_session is an active session passed by the caller.
    Returns (InvoiceDB instance in pg_session or None, error message or 'skipped_duplicate' or None).
    """
    # Check if invoice_number already exists in PostgreSQL
    existing_pg_invoice = pg_session.query(InvoiceDB).filter(
        InvoiceDB.invoice_number == local_invoice_db.invoice_number).first()
    if existing_pg_invoice:
        logger.info(
            f"Invoice {local_invoice_db.invoice_number} already exists in PostgreSQL. Skipping transfer, marking local as synced.")
        return existing_pg_invoice, "skipped_duplicate"

    # Create a new InvoiceDB for PostgreSQL session from the local InvoiceDB data
    pg_invoice = InvoiceDB(
        invoice_number=local_invoice_db.invoice_number,
        invoice_date=local_invoice_db.invoice_date,  # Already a date object
        customer_name=local_invoice_db.customer_name,
        customer_address=local_invoice_db.customer_address,
        is_synced=True  # Mark as synced in PostgreSQL context
    )
    for local_item in local_invoice_db.line_items:
        pg_item = LineItemDB(
            description=local_item.description,
            quantity=local_item.quantity,  # Already Decimal
            unit_price=local_item.unit_price  # Already Decimal
        )
        pg_invoice.line_items.append(pg_item)

    try:
        pg_session.add(pg_invoice)
        # Commit will happen outside if part of a larger transaction (e.g. syncing multiple)
        # For a single transfer, commit here or let caller handle it.
        # pg_session.commit() # If committing one by one.
        # pg_session.refresh(pg_invoice)
        logger.info(f"Invoice {pg_invoice.invoice_number} prepared for PostgreSQL session.")
        return pg_invoice, None  # Returns the object to be committed by caller
    except IntegrityError as e:  # Should ideally be caught by the pre-check
        pg_session.rollback()
        logger.error(f"Integrity error transferring invoice {local_invoice_db.invoice_number} to PG: {e}",
                     exc_info=True)
        return None, f"Database integrity error: {e}"
    except SQLAlchemyError as e:
        pg_session.rollback()
        logger.error(f"SQLAlchemy error transferring invoice {local_invoice_db.invoice_number} to PG: {e}",
                     exc_info=True)
        return None, f"Database error: {e}"


# Example of a utility function if needed
def get_next_invoice_number_from_db(prefix: str = "INV-") -> str:
    """
    Generates a suggestion for the next invoice number based on existing ones in PG.
    This is a basic example; robust sequence generation can be complex.
    """
    session = get_postgres_session()
    if not session:
        # Fallback if PG not available, could use local or just a simple date based
        return f"{prefix}{PythonDate.today().strftime('%Y%m%d')}-001"
    try:
        today_prefix = f"{prefix}{PythonDate.today().strftime('%Y%m%d')}-"
        # Find the max number for today's date
        last_invoice = session.query(InvoiceDB.invoice_number) \
            .filter(InvoiceDB.invoice_number.like(f"{today_prefix}%")) \
            .order_by(func.substr(InvoiceDB.invoice_number, len(today_prefix) + 1).cast(Integer).desc()) \
            .first()

        if last_invoice:
            last_num_str = last_invoice[0].split('-')[-1]
            next_num = int(last_num_str) + 1
            return f"{today_prefix}{next_num:03d}"
        else:
            return f"{today_prefix}001"
    except SQLAlchemyError as e:
        logger.error(f"Could not fetch next invoice number from DB: {e}", exc_info=True)
        return f"{today_prefix}001"  # Fallback
    finally:
        if session:
            session.close()


def get_unsynced_invoices_local():
    return None


def mark_invoice_as_synced_local():
    return None


def initialize_postgres_engine():
    return None


def transfer_invoice_to_postgres():
    return None