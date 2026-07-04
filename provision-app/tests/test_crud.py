from datetime import datetime, date
from app.models import ExpenseEntry, ScheduledRule
from app.schemas import ExpenseCreate, ScheduledRuleCreate

# --- UNIT TESTS FOR DATABASE DIRECT OPERATIONS ---

def test_create_expense_direct(db):
    expense = ExpenseEntry(
        amount=-50.0,
        date=datetime(2026, 7, 4),
        description="Weekly Tesco grocery trip",
        user="simone",
        expense_type=11
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    assert expense.id is not None
    assert expense.amount == -50.0
    assert expense.description == "Weekly Tesco grocery trip"
    
    # Retrieve
    db_exp = db.query(ExpenseEntry).filter_by(id=expense.id).first()
    assert db_exp is not None
    assert db_exp.user == "simone"


def test_create_scheduled_rule_direct(db):
    rule = ScheduledRule(
        description="Electricity Bill",
        amount=-85.0,
        day_of_month=12,
        rule_type="direct_debit",
        user="directdebit",
        is_active=True
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    assert rule.id is not None
    assert rule.day_of_month == 12
    assert rule.is_active is True


# --- INTEGRATION TESTS FOR WEB ENDPOINTS (CLIENT) ---

def test_read_dashboard(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Dashboard" in response.text
    # Check if UI components exist
    assert "Spent This Month" in response.text
    assert "Net Balance" in response.text


def test_create_expense_via_api(client, db):
    # Form post to /expenses/new
    form_data = {
        "description": "Internet Subscription",
        "amount": "-25.00",
        "date": "2026-07-04",
        "user": "directdebit",
        "expense_type": "1"
    }
    response = client.post("/expenses/new", data=form_data)
    assert response.status_code == 200
    
    # Verify row HTML elements are returned
    assert "Internet Subscription" in response.text
    assert "directdebit" in response.text
    assert "-25.00" in response.text
    
    # Check database
    db_exp = db.query(ExpenseEntry).filter_by(description="Internet Subscription").first()
    assert db_exp is not None
    assert db_exp.amount == -25.0


def test_search_expenses(client, db):
    # Setup some test expenses
    exp1 = ExpenseEntry(amount=-15.0, date=datetime(2026, 7, 1), description="Coffee with Linda", user="simone", expense_type=1)
    exp2 = ExpenseEntry(amount=-95.0, date=datetime(2026, 7, 2), description="Weekly Groceries", user="marco", expense_type=11)
    db.add_all([exp1, exp2])
    db.commit()
    
    # Search for "Linda"
    response = client.get("/expenses/search?search=Linda")
    assert response.status_code == 200
    assert "Coffee with Linda" in response.text
    assert "Weekly Groceries" not in response.text
    
    # Filter by user
    response = client.get("/expenses/search?user_filter=marco")
    assert response.status_code == 200
    assert "Weekly Groceries" in response.text
    assert "Coffee with Linda" not in response.text


def test_edit_expense_via_api(client, db):
    exp = ExpenseEntry(amount=-10.0, date=datetime(2026, 7, 1), description="Snack", user="simone")
    db.add(exp)
    db.commit()
    db.refresh(exp)
    
    form_data = {
        "description": "Premium Snack",
        "amount": "-12.50",
        "date": "2026-07-01",
        "user": "simone",
        "expense_type": ""
    }
    
    response = client.post(f"/expenses/{exp.id}/edit", data=form_data)
    assert response.status_code == 200
    assert "Premium Snack" in response.text
    assert "-12.50" in response.text
    
    # Check DB update
    db.refresh(exp)
    assert exp.description == "Premium Snack"
    assert exp.amount == -12.50


def test_delete_expense_via_api(client, db):
    exp = ExpenseEntry(amount=-100.0, date=datetime(2026, 7, 1), description="Rent Deposit", user="marco")
    db.add(exp)
    db.commit()
    db.refresh(exp)
    
    response = client.delete(f"/expenses/{exp.id}")
    assert response.status_code == 200
    
    # Check DB deletion
    db_exp = db.query(ExpenseEntry).filter_by(id=exp.id).first()
    assert db_exp is None


def test_bulk_upload_execution(client, db):
    # Add rules
    rule1 = ScheduledRule(description="Water Charge", amount=-30.0, day_of_month=1, rule_type="direct_debit", user="directdebit", is_active=True)
    rule2 = ScheduledRule(description="Tesco Allowance", amount=-300.0, day_of_month=28, rule_type="lump_sum", user="bulkupload", is_active=True)
    rule3 = ScheduledRule(description="Disabled Rule", amount=-50.0, day_of_month=15, rule_type="direct_debit", user="directdebit", is_active=False)
    db.add_all([rule1, rule2, rule3])
    db.commit()
    
    # Submit bulk upload form
    form_data = {
        "target_month": "7",
        "target_year": "2026",
        f"rule_enabled_{rule1.id}": "true",
        f"rule_amount_{rule1.id}": "-32.50", # Modify amount
        f"rule_enabled_{rule2.id}": "true",
        f"rule_amount_{rule2.id}": "-300.00",
        # rule 3 is disabled in DB, and not selected in form
    }
    
    response = client.post("/bulk-upload/submit", data=form_data)
    assert response.status_code == 200
    assert "Bulk Provisioning Completed!" in response.text
    assert "Water Charge" in response.text
    assert "Tesco Allowance" in response.text
    
    # Check expenses created in DB
    expenses = db.query(ExpenseEntry).all()
    assert len(expenses) == 2
    
    exp_water = next(e for e in expenses if "Water Charge" in e.description)
    assert exp_water.amount == -32.50 # Changed value should persist
    assert exp_water.date.date() == date(2026, 7, 1)
    
    exp_tesco = next(e for e in expenses if "Tesco Allowance" in e.description)
    assert exp_tesco.amount == -300.00
    assert exp_tesco.date.date() == date(2026, 7, 28)
