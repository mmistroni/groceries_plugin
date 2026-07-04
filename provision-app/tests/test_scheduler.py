from datetime import date, datetime, timedelta
from app.models import ExpenseEntry, ScheduledRule
from app.scheduler import process_scheduled_insertions

def test_scheduler_inserts_due_rules(db):
    # Rule 1: Due on day 5, current date is day 6. Should insert.
    rule1 = ScheduledRule(
        description="Netflix",
        amount=-10.0,
        day_of_month=5,
        rule_type="direct_debit",
        is_active=True,
        last_run=None
    )
    # Rule 2: Due on day 15, current date is day 6. Should NOT insert.
    rule2 = ScheduledRule(
        description="Gym Membership",
        amount=-35.0,
        day_of_month=15,
        rule_type="direct_debit",
        is_active=True,
        last_run=None
    )
    db.add_all([rule1, rule2])
    db.commit()
    
    # Process for day 6
    target = date(2026, 7, 6)
    inserted = process_scheduled_insertions(db, target_date=target)
    
    assert len(inserted) == 1
    assert inserted[0].description == "Netflix"
    assert inserted[0].amount == -10.0
    # Backdated to the rule's designated day
    assert inserted[0].date == datetime(2026, 7, 5)
    
    # Rule 1's last_run should be updated
    db.refresh(rule1)
    db.refresh(rule2)
    assert rule1.last_run == target
    assert rule2.last_run is None


def test_scheduler_avoids_duplicate_runs_same_month(db):
    rule = ScheduledRule(
        description="Electricity Bill",
        amount=-50.0,
        day_of_month=1,
        rule_type="direct_debit",
        is_active=True,
        last_run=date(2026, 7, 1) # Already run in July
    )
    db.add(rule)
    db.commit()
    
    # Attempt to process on July 5
    inserted = process_scheduled_insertions(db, target_date=date(2026, 7, 5))
    
    # Should not insert since it's already run in the current month (July)
    assert len(inserted) == 0


def test_scheduler_runs_in_new_month_after_completion(db):
    rule = ScheduledRule(
        description="Electricity Bill",
        amount=-50.0,
        day_of_month=1,
        rule_type="direct_debit",
        is_active=True,
        last_run=date(2026, 6, 1) # Run in June, now we are in July
    )
    db.add(rule)
    db.commit()
    
    # Process on July 2
    inserted = process_scheduled_insertions(db, target_date=date(2026, 7, 2))
    
    assert len(inserted) == 1
    assert inserted[0].description == "Electricity Bill"
    assert inserted[0].date == datetime(2026, 7, 1)
    
    db.refresh(rule)
    assert rule.last_run == date(2026, 7, 2)


def test_scheduler_inactive_rules_ignored(db):
    rule = ScheduledRule(
        description="Canceled Sub",
        amount=-15.0,
        day_of_month=1,
        rule_type="direct_debit",
        is_active=False,
        last_run=None
    )
    db.add(rule)
    db.commit()
    
    inserted = process_scheduled_insertions(db, target_date=date(2026, 7, 2))
    assert len(inserted) == 0
