from datetime import datetime, date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .config import settings
from .models import Base, ExpenseEntry, ScheduledRule

# Configure sqlite specifically for thread safety in local development
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def seed_database(db: Session):
    # Check if database has already been seeded to prevent duplicates
    if db.query(ExpenseEntry).count() > 0 or db.query(ScheduledRule).count() > 0:
        return
    
    # 1. Seed Scheduled Rules (Direct debits and monthly lump sums)
    rules = [
        ScheduledRule(
            description="COUNCIL Tax",
            amount=-167.0,
            day_of_month=5,
            rule_type="direct_debit",
            expense_type=9,
            user="directdebit",
            is_active=True
        ),
        ScheduledRule(
            description="Water Direct Debit",
            amount=-31.0,
            day_of_month=1,
            rule_type="direct_debit",
            expense_type=5,
            user="directdebit",
            is_active=True
        ),
        ScheduledRule(
            description="GAS Direct Debit",
            amount=-64.0,
            day_of_month=1,
            rule_type="direct_debit",
            expense_type=6,
            user="directdebit",
            is_active=True
        ),
        ScheduledRule(
            description="TV License",
            amount=-12.0,
            day_of_month=1,
            rule_type="direct_debit",
            expense_type=10,
            user="directdebit",
            is_active=True
        ),
        ScheduledRule(
            description="Trentbridge Mortgage",
            amount=-279.0,
            day_of_month=1,
            rule_type="direct_debit",
            expense_type=13,
            user="directdebit",
            is_active=True
        ),
        # Monthly lump-sums (represented as rules with type "lump_sum")
        ScheduledRule(
            description="groceries allowance",
            amount=-400.0,
            day_of_month=28,
            rule_type="lump_sum",
            expense_type=11,
            user="bulkupload",
            is_active=True
        ),
        ScheduledRule(
            description="petrol allowance",
            amount=-150.0,
            day_of_month=28,
            rule_type="lump_sum",
            expense_type=8,
            user="bulkupload",
            is_active=True
        ),
        ScheduledRule(
            description="rent allowance",
            amount=-800.0,
            day_of_month=28,
            rule_type="lump_sum",
            expense_type=13,
            user="bulkupload",
            is_active=True
        )
    ]
    db.add_all(rules)
    db.commit()
    
    # 2. Seed Mock Expense Entries
    today = date.today()
    last_month = today - timedelta(days=30)
    
    mock_expenses = [
        ExpenseEntry(
            amount=-10.0,
            date=datetime.combine(last_month, datetime.min.time()),
            description="Food for Martin's dinner",
            user="simone",
            expense_type=1
        ),
        ExpenseEntry(
            amount=90.0,
            date=datetime.combine(last_month, datetime.min.time()),
            description="Simone's food reimbursement",
            user="simone",
            expense_type=1
        ),
        ExpenseEntry(
            amount=-60.0,
            date=datetime.combine(last_month, datetime.min.time()),
            description="groceries",
            user="marco",
            expense_type=11
        ),
        ExpenseEntry(
            amount=-35.0,
            date=datetime.combine(today - timedelta(days=10), datetime.min.time()),
            description="chubby panda dinner",
            user="marco and simone",
            expense_type=2
        ),
        ExpenseEntry(
            amount=-31.0,
            date=datetime.combine(today - timedelta(days=15), datetime.min.time()),
            description="Water Bill Payment",
            user="directdebit",
            expense_type=5
        ),
        ExpenseEntry(
            amount=-400.0,
            date=datetime.combine(today - timedelta(days=5), datetime.min.time()),
            description="groceries allowance upload",
            user="bulkupload",
            expense_type=11
        ),
        ExpenseEntry(
            amount=-150.0,
            date=datetime.combine(today - timedelta(days=5), datetime.min.time()),
            description="petrol allowance upload",
            user="bulkupload",
            expense_type=8
        )
    ]
    db.add_all(mock_expenses)
    db.commit()
