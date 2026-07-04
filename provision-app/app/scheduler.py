from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from .models import ExpenseEntry, ScheduledRule

def process_scheduled_insertions(db: Session, target_date: date = None) -> list:
    """
    Process automated expense insertions for active scheduled rules.
    Runs through each active rule: if the target_date's day is >= the rule's day_of_month
    and it hasn't been executed yet in the target_date's month, it inserts an expense.
    """
    if target_date is None:
        target_date = date.today()
        
    inserted_expenses = []
    
    # Get active scheduled rules
    active_rules = db.query(ScheduledRule).filter(ScheduledRule.is_active == True).all()
    
    for rule in active_rules:
        # Check if the rule was already run in the target month/year
        already_run = False
        if rule.last_run:
            already_run = (rule.last_run.year == target_date.year and 
                           rule.last_run.month == target_date.month)
            
        # If not run and the day of the month has arrived/passed (catch up)
        if not already_run and target_date.day >= rule.day_of_month:
            # Determine the exact insertion date (designated day of the current month)
            try:
                insertion_date = date(target_date.year, target_date.month, rule.day_of_month)
            except ValueError:
                # Handle end-of-month cases (e.g. day 31 in a 30-day month)
                # Rollback to last day of the month
                if target_date.month == 12:
                    insertion_date = date(target_date.year, 12, 31)
                else:
                    insertion_date = date(target_date.year, target_date.month + 1, 1) - timedelta(days=1)
            
            # Create the expense entry
            new_expense = ExpenseEntry(
                amount=rule.amount,
                date=datetime.combine(insertion_date, datetime.min.time()),
                description=rule.description,
                user=rule.user,
                expense_type=rule.expense_type
            )
            db.add(new_expense)
            
            # Update rule run status
            rule.last_run = target_date
            inserted_expenses.append(new_expense)
            
    if inserted_expenses:
        db.commit()
        # Refresh inserted expenses to bind them to the session
        for exp in inserted_expenses:
            db.refresh(exp)
            
    return inserted_expenses
