# database/models.py
"""
SQLAlchemy table definitions (ORM models) for storing invoice data.
"""
from sqlalchemy import Column, Integer, String, Float, Date as SQLDate, Boolean, ForeignKey, Text, Numeric
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import date as PythonDate

Base = declarative_base()


class InvoiceDB(Base):
    __tablename__ = 'invoices_master'  # Changed name to avoid potential clash with business model if imported same namespace

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_number = Column(String(50), nullable=False, unique=True, index=True)
    # Storing date as native SQL Date type is best for DB operations
    invoice_date = Column(SQLDate, nullable=False)
    customer_name = Column(String(255), nullable=False)
    customer_address = Column(Text)

    # Total amount could be calculated or stored. For consistency, let's calculate.
    # total_amount = Column(Numeric(10, 2), nullable=False) # Example for fixed-point decimal

    is_synced = Column(Boolean, default=False, nullable=False, index=True)  # For SQLite sync tracking

    line_items = relationship("LineItemDB", back_populates="invoice", cascade="all, delete-orphan")

    @hybrid_property
    def total_amount(self) -> float:
        if self.line_items:
            return sum(item.subtotal for item in self.line_items if item.subtotal is not None)
        return 0.0

    def __repr__(self) -> str:
        return (f"<InvoiceDB(id={self.id}, invoice_number='{self.invoice_number}', "
                f"date='{self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else 'N/A'}', synced={self.is_synced})>")


class LineItemDB(Base):
    __tablename__ = 'invoice_line_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey('invoices_master.id', ondelete="CASCADE"), nullable=False, index=True)

    description = Column(Text, nullable=False)
    # Use Numeric for currency/financial values to avoid floating point issues
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    invoice = relationship("InvoiceDB", back_populates="line_items")

    @hybrid_property
    def subtotal(self) -> float:
        if self.quantity is not None and self.unit_price is not None:
            return float(self.quantity * self.unit_price)  # Convert back to float for Python use
        return 0.0

    def __repr__(self) -> str:
        return (f"<LineItemDB(id={self.id}, description='{self.description[:20]}...', "
                f"quantity={self.quantity}, unit_price={self.unit_price})>")