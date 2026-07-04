from sqlalchemy import Column, Integer, BigInteger, Float, String, DateTime, Boolean, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ExpenseEntry(Base):
    __tablename__ = "EXPENSE_ENTRY"
    
    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    amount = Column("AMOUNT", Float)
    date = Column("DATE", DateTime)
    description = Column("DESCRIPTION", String(255))
    user = Column("USER", String(255))
    expense_type = Column("EXPENSE_TYPE", Integer, nullable=True)

class ScheduledRule(Base):
    __tablename__ = "SCHEDULED_RULE"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    day_of_month = Column(Integer, nullable=False)  # 1 to 31
    rule_type = Column(String(50), nullable=False)    # 'direct_debit' or 'lump_sum'
    expense_type = Column(Integer, nullable=True)
    user = Column(String(255), default="directdebit")
    is_active = Column(Boolean, default=True)
    last_run = Column(Date, nullable=True)           # Track date when this was last automated (e.g., to prevent double runs)
