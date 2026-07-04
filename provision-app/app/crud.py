from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from typing import Optional
from .models import ExpenseEntry, ScheduledRule
from .schemas import ExpenseCreate, ExpenseUpdate, ScheduledRuleCreate, ScheduledRuleUpdate

# Expense CRUD Operations
def get_expense(db: Session, expense_id: int):
    return db.query(ExpenseEntry).filter(ExpenseEntry.id == expense_id).first()

def get_expenses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    user: Optional[str] = None,
    expense_type: Optional[int] = None
):
    query = db.query(ExpenseEntry)
    if search:
        query = query.filter(
            or_(
                ExpenseEntry.description.ilike(f"%{search}%"),
                ExpenseEntry.user.ilike(f"%{search}%")
            )
        )
    if user:
        query = query.filter(ExpenseEntry.user == user)
    if expense_type is not None:
        query = query.filter(ExpenseEntry.expense_type == expense_type)
        
    return query.order_by(ExpenseEntry.date.desc()).offset(skip).limit(limit).all()

def create_expense(db: Session, expense: ExpenseCreate):
    db_expense = ExpenseEntry(
        amount=expense.amount,
        date=expense.date,
        description=expense.description,
        user=expense.user,
        expense_type=expense.expense_type
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def update_expense(db: Session, expense_id: int, expense: ExpenseUpdate):
    db_expense = get_expense(db, expense_id)
    if not db_expense:
        return None
    for var, val in expense.model_dump(exclude_unset=True).items():
        setattr(db_expense, var, val)
    db.commit()
    db.refresh(db_expense)
    return db_expense

def delete_expense(db: Session, expense_id: int):
    db_expense = get_expense(db, expense_id)
    if db_expense:
        db.delete(db_expense)
        db.commit()
        return True
    return False

# Scheduled Rules CRUD Operations
def get_scheduled_rule(db: Session, rule_id: int):
    return db.query(ScheduledRule).filter(ScheduledRule.id == rule_id).first()

def get_scheduled_rules(db: Session, active_only: bool = False):
    query = db.query(ScheduledRule)
    if active_only:
        query = query.filter(ScheduledRule.is_active == True)
    return query.all()

def create_scheduled_rule(db: Session, rule: ScheduledRuleCreate):
    db_rule = ScheduledRule(
        description=rule.description,
        amount=rule.amount,
        day_of_month=rule.day_of_month,
        rule_type=rule.rule_type,
        expense_type=rule.expense_type,
        user=rule.user,
        is_active=rule.is_active
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def update_scheduled_rule(db: Session, rule_id: int, rule: ScheduledRuleUpdate):
    db_rule = get_scheduled_rule(db, rule_id)
    if not db_rule:
        return None
    for var, val in rule.model_dump(exclude_unset=True).items():
        setattr(db_rule, var, val)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def delete_scheduled_rule(db: Session, rule_id: int):
    db_rule = get_scheduled_rule(db, rule_id)
    if db_rule:
        db.delete(db_rule)
        db.commit()
        return True
    return False
