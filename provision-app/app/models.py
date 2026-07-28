# models.py
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Date
from sqlalchemy.orm import declarative_base
from .enums import ExpenseTypeColumn  # import your new type

Base = declarative_base()

class ExpenseEntry(Base):
    __tablename__ = "EXPENSE_ENTRY"
    
    id = Column("ID", Integer, primary_key=True, autoincrement=True)
    amount = Column("AMOUNT", Float)
    date = Column("DATE", DateTime)
    description = Column("DESCRIPTION", String(255))
    user = Column("USER", String(255))
    # Updated column type here
    expense_type = Column("EXPENSE_TYPE", ExpenseTypeColumn, nullable=True)


class ScheduledRule(Base):
    __tablename__ = "SCHEDULED_RULE"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    day_of_month = Column(Integer, nullable=False)
    rule_type = Column(String(50), nullable=False)
    # Updated column type here
    expense_type = Column(ExpenseTypeColumn, nullable=True)
    user = Column(String(255), default="directdebit")
    is_active = Column(Boolean, default=True)
    last_run = Column(Date, nullable=True)