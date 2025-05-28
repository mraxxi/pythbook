from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, Transaction
from config.config_manager import load_config
import os
from datetime import date as DDate # Alias to avoid conflict with Transaction.date

# Load configuration
config = load_config()

# --- SQLite Setup ---
# Determine the path for the SQLite database relative to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SQLITE_DB_PATH = os.path.join(project_root, config.get('sqlite_db_name', 'local_transactions.db'))
sqlite_engine = create_engine(f'sqlite:///{SQLITE_DB_PATH}')
Base.metadata.create_all(sqlite_engine) # Ensure table is created
SQLiteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)

# --- PostgreSQL Setup ---
pg_config = config.get('postgres', {})
POSTGRES_URL = None
postgres_engine = None
PostgreSQLSessionLocal = None

def get_postgres_url():
    pg_conf = load_config().get('postgres', {}) # Reload fresh config
    if pg_conf.get('user') and pg_conf.get('password') and pg_conf.get('host') and pg_conf.get('database'):
        return f"postgresql://{pg_conf['user']}:{pg_conf['password']}@{pg_conf['host']}:{pg_conf.get('port', 5432)}/{pg_conf['database']}"
    return None

def initialize_postgres_engine():
    global postgres_engine, PostgreSQLSessionLocal, POSTGRES_URL
    POSTGRES_URL = get_postgres_url()
    if POSTGRES_URL:
        try:
            postgres_engine = create_engine(POSTGRES_URL)
            Base.metadata.create_all(postgres_engine) # Ensure table is created
            PostgreSQLSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)
            return True
        except Exception as e:
            print(f"Failed to connect to PostgreSQL: {e}")
            postgres_engine = None
            PostgreSQLSessionLocal = None
            return False
    return False

# Initialize PostgreSQL engine on module load or explicitly call it
initialize_postgres_engine()


def get_sqlite_session() -> Session:
    return SQLiteSessionLocal()

def get_postgres_session() -> Session:
    if not PostgreSQLSessionLocal and not initialize_postgres_engine():
        raise ConnectionError("PostgreSQL is not configured or connection failed.")
    return PostgreSQLSessionLocal()

def add_transaction_local(db: Session, transaction_data: dict):
    """Adds a transaction to the local SQLite database."""
    new_transaction = Transaction(
        date=transaction_data['date'],
        amount=transaction_data['amount'],
        category=transaction_data['category'],
        description=transaction_data.get('description'),
        payment_method=transaction_data.get('payment_method'),
        is_synced=transaction_data.get('is_synced', False) # Default to False for local saves
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

def add_transaction_postgres(db: Session, transaction_data: dict):
    """Adds a transaction to the PostgreSQL database."""
    # When adding to Postgres, it's inherently "synced" from the perspective of the master DB
    new_transaction = Transaction(
        date=transaction_data['date'],
        amount=transaction_data['amount'],
        category=transaction_data['category'],
        description=transaction_data.get('description'),
        payment_method=transaction_data.get('payment_method'),
        is_synced=True # Or you might omit this if not needed in Postgres table
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    return new_transaction

def get_unsynced_transactions_local(db: Session):
    """Retrieves all unsynced transactions from local SQLite."""
    return db.query(Transaction).filter(Transaction.is_synced == False).all()

def mark_transaction_as_synced_local(db: Session, transaction_id: int):
    """Marks a specific transaction as synced in the local SQLite database."""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if transaction:
        transaction.is_synced = True
        db.commit()