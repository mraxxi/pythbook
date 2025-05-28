from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(String(255))
    payment_method = Column(String(50))
    # This field is primarily for the local SQLite DB
    # to track which records need to be synced to PostgreSQL.
    is_synced = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Transaction(id={self.id}, date='{self.date}', amount={self.amount}, category='{self.category}', synced={self.is_synced})>"

# Example of how you might create an engine and session (more in db_handler.py)
# sqlite_engine = create_engine('sqlite:///local_transactions.db')
# Base.metadata.create_all(sqlite_engine) # Creates the table if it doesn't exist

# postgres_engine = create_engine('postgresql://user:password@host:port/database')
# Base.metadata.create_all(postgres_engine) # Creates the table if it doesn't exist