from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from .models import ExpenseEntry, ScheduledRule


def calculate_as_of_date(year: int, month: int, day_of_month: int) -> date:
    """
    Calculates the exact as-of date for a given year, month, and rule day.
    Automatically caps the day to the last valid day of that specific month.
    """
    _, max_days = monthrange(year, month)
    target_day = min(day_of_month, max_days)
    return date(year, month, target_day)


def is_rule_due(rule: ScheduledRule, target_date: date) -> bool:
    """
    Checks if a rule is due for execution in the target_date's month and year,
    and whether the target_date has reached or passed the rule's day of the month.
    """
    if not rule.is_active:
        return False

    already_run = False
    if rule.last_run:
        already_run = (
            rule.last_run.year == target_date.year and 
            rule.last_run.month == target_date.month
        )

    as_of_date = calculate_as_of_date(target_date.year, target_date.month, rule.day_of_month)
    return not already_run and target_date >= as_of_date


def process_scheduled_insertions(db: Session, target_date: Optional[date] = None) -> List[ExpenseEntry]:
    """
    Process automated expense insertions for active scheduled rules.
    Inserts backdated expenses based on each rule's exact day_of_month (as_of_date).
    """
    if target_date is None:
        target_date = date.today()

    inserted_expenses = []
    active_rules = db.query(ScheduledRule).filter(ScheduledRule.is_active == True).all()

    for rule in active_rules:
        if is_rule_due(rule, target_date):
            # Compute the exact backdated date for this expense entry
            insertion_date = calculate_as_of_date(target_date.year, target_date.month, rule.day_of_month)

            # Create the backdated expense entry
            new_expense = ExpenseEntry(
                amount=rule.amount,
                date=datetime.combine(insertion_date, datetime.min.time()),
                description=rule.description,
                user=rule.user,
                expense_type=rule.expense_type
            )
            db.add(new_expense)

            # Update rule execution state
            rule.last_run = target_date
            inserted_expenses.append(new_expense)

    if inserted_expenses:
        db.commit()
        for exp in inserted_expenses:
            db.refresh(exp)

    return inserted_expenses


def run_startup_catchup(db: Session) -> List[ExpenseEntry]:
    """
    Convenience wrapper to execute pending rules upon application startup or cold start.
    """
    return process_scheduled_insertions(db, target_date=date.today())