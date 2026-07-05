import os
from contextlib import asynccontextmanager
from datetime import datetime, date
from typing import Optional

from fastapi import FastAPI, Depends, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import extract

from .config import settings
from .database import engine, SessionLocal, get_db, seed_database
from .models import Base, ExpenseEntry, ScheduledRule
from .schemas import ExpenseCreate, ExpenseUpdate, ScheduledRuleCreate, ScheduledRuleUpdate
from . import crud
from .scheduler import process_scheduled_insertions

# Create database tables and seed if necessary on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    # Seed mock data
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

# Setup Jinja2 templates
# Look up template directory relative to app path
current_dir = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

# Inject settings helper in templates
templates.env.globals["settings"] = settings
templates.env.globals["datetime"] = datetime

# --- UI PAGES ROUTING ---

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db: Session = Depends(get_db)):
    # Calculate stats for the current month
    today = date.today()
    expenses = db.query(ExpenseEntry).filter(
        extract('year', ExpenseEntry.date) == today.year,
        extract('month', ExpenseEntry.date) == today.month
    ).all()
    
    # Calculate Spent (negative amounts)
    total_spent = sum(e.amount for e in expenses if e.amount < 0)
    # Calculate Income/Reimbursements (positive amounts)
    total_income = sum(e.amount for e in expenses if e.amount > 0)
    net_balance = sum(e.amount for e in expenses)
    
    # Scheduled rules details
    rules = db.query(ScheduledRule).filter(ScheduledRule.is_active == True).all()
    active_dd_count = sum(1 for r in rules if r.rule_type == 'direct_debit')
    active_dd_total = sum(r.amount for r in rules if r.rule_type == 'direct_debit')
    lump_sum_total = sum(r.amount for r in rules if r.rule_type == 'lump_sum')
    
    # Get 5 recent expenses
    recent = db.query(ExpenseEntry).order_by(ExpenseEntry.date.desc()).limit(5).all()
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "title": "Dashboard",
            "active_page": "dashboard",
            "total_spent_this_month": total_spent,
            "active_dd_count": active_dd_count,
            "active_dd_total": active_dd_total,
            "lump_sum_total": lump_sum_total,
            "net_balance": net_balance,
            "recent_expenses": recent
        }
    )

@app.get("/expenses", response_class=HTMLResponse)
async def read_expenses(request: Request, db: Session = Depends(get_db)):
    expenses = crud.get_expenses(db, limit=100)
    return templates.TemplateResponse(
        request=request,
        name="expenses.html",
        context={
            "title": "Expenses Log",
            "active_page": "expenses",
            "expenses": expenses
        }
    )

@app.get("/bulk-upload", response_class=HTMLResponse)
async def read_bulk_upload(request: Request, db: Session = Depends(get_db)):
    rules = crud.get_scheduled_rules(db, active_only=True)
    today = date.today()
    return templates.TemplateResponse(
        request=request,
        name="bulk_upload.html",
        context={
            "title": "Bulk Upload",
            "active_page": "bulk-upload",
            "rules": rules,
            "current_month": today.month,
            "current_year": today.year
        }
    )

@app.get("/admin-settings", response_class=HTMLResponse)
async def read_admin_settings(request: Request, db: Session = Depends(get_db)):
    rules = crud.get_scheduled_rules(db)
    return templates.TemplateResponse(
        request=request,
        name="admin_settings.html",
        context={
            "title": "Scheduled Rules Configuration",
            "active_page": "admin-settings",
            "rules": rules
        }
    )

# --- HTMX / AJAX CRUD ROUTES ---

# Search / Filter Expenses (returns list rows)
@app.get("/expenses/search", response_class=HTMLResponse)
async def search_expenses(
    request: Request,
    search: Optional[str] = None,
    user_filter: Optional[str] = None,
    category_filter: Optional[int] = None,
    db: Session = Depends(get_db)
):

    # 2. Safely parse into an integer only if it's a numeric string
    category_id = int(category_filter) if isinstance(category_filter, str) and category_filter.isdigit() else None
    
    expenses = crud.get_expenses(
        db, 
        search=search, 
        user=user_filter or None, 
        expense_type=category_id
    )
    
    if not expenses:
        return "<tr><td colspan='6' class='py-12 text-center text-slate-500'><i class='fa-solid fa-receipt text-4xl mb-3 block'></i>No matching expenses found.</td></tr>"
        
    html = ""
    for expense in expenses:
        html += templates.get_template("partials/expense_row.html").render({"expense": expense})
    return html

# Get Single Expense Row (view mode)
@app.get("/expenses/{expense_id}", response_class=HTMLResponse)
async def get_expense_row(request: Request, expense_id: int, db: Session = Depends(get_db)):
    expense = crud.get_expense(db, expense_id)
    return templates.TemplateResponse(request=request, name="partials/expense_row.html", context={"expense": expense})

# Create Expense Form (inline)
@app.get("/expenses/new", response_class=HTMLResponse)
async def new_expense_form(request: Request):
    today_str = date.today().strftime('%Y-%m-%d')
    return templates.TemplateResponse(
        request=request,
        name="partials/expense_form.html",
        context={
            "expense": None,
            "today_str": today_str
        }
    )

# Create Expense Submission (inline)
@app.post("/expenses/new", response_class=HTMLResponse)
async def create_expense_endpoint(
    request: Request,
    description: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...),
    user: str = Form(...),
    expense_type: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    dt = datetime.strptime(date, "%Y-%m-%d")
    expense_in = ExpenseCreate(
        description=description,
        amount=amount,
        date=dt,
        user=user,
        expense_type=expense_type
    )
    expense = crud.create_expense(db, expense_in)
    return templates.TemplateResponse(request=request, name="partials/expense_row.html", context={"expense": expense})

# Quick Add from Dashboard
@app.post("/expenses/quick", response_class=HTMLResponse)
async def quick_add_endpoint(
    request: Request,
    description: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...),
    user: str = Form(...),
    expense_type: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    dt = datetime.strptime(date, "%Y-%m-%d")
    expense_in = ExpenseCreate(
        description=description,
        amount=amount,
        date=dt,
        user=user,
        expense_type=expense_type
    )
    expense = crud.create_expense(db, expense_in)
    
    # Returns the recent expense row markup to prepend
    return templates.get_template("partials/expense_row.html").render({"expense": expense})

# Edit Expense Form (inline swap)
@app.get("/expenses/{expense_id}/edit", response_class=HTMLResponse)
async def edit_expense_form(request: Request, expense_id: int, db: Session = Depends(get_db)):
    expense = crud.get_expense(db, expense_id)
    return templates.TemplateResponse(request=request, name="partials/expense_form.html", context={"expense": expense})

# Edit Expense Submission
@app.post("/expenses/{expense_id}/edit", response_class=HTMLResponse)
async def update_expense_endpoint(
    request: Request,
    expense_id: int,
    description: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...),
    user: str = Form(...),
    expense_type: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    dt = datetime.strptime(date, "%Y-%m-%d")
    expense_in = ExpenseUpdate(
        description=description,
        amount=amount,
        date=dt,
        user=user,
        expense_type=expense_type
    )
    expense = crud.update_expense(db, expense_id, expense_in)
    return templates.TemplateResponse(request=request, name="partials/expense_row.html", context={"expense": expense})

# Delete Expense
@app.delete("/expenses/{expense_id}", response_class=HTMLResponse)
async def delete_expense_endpoint(expense_id: int, db: Session = Depends(get_db)):
    crud.delete_expense(db, expense_id)
    return Response(status_code=200)

# --- BULK PROVISIONING ROUTE ---

@app.post("/bulk-upload/submit", response_class=HTMLResponse)
async def submit_bulk_upload(
    request: Request,
    target_month: int = Form(...),
    target_year: int = Form(...),
    db: Session = Depends(get_db)
):
    # Read all form data to check enabled items
    form_data = await request.form()
    
    inserted = []
    active_rules = crud.get_scheduled_rules(db, active_only=True)
    
    for rule in active_rules:
        # Check if the specific checkbox was checked
        is_enabled = form_data.get(f"rule_enabled_{rule.id}") == "true"
        if is_enabled:
            # Read updated amount
            custom_amount_str = form_data.get(f"rule_amount_{rule.id}")
            amount = float(custom_amount_str) if custom_amount_str else rule.amount
            
            # Construct date
            day = min(rule.day_of_month, 28) # Default safety boundary
            try:
                upload_date = date(target_year, target_month, rule.day_of_month)
            except ValueError:
                # Handle calendar boundary (Feb 29 etc)
                if target_month == 2:
                    upload_date = date(target_year, 2, 28)
                elif target_month in [4, 6, 9, 11] and rule.day_of_month == 31:
                    upload_date = date(target_year, target_month, 30)
                else:
                    upload_date = date(target_year, target_month, 28)
            
            # Insert into database
            expense_in = ExpenseCreate(
                amount=amount,
                date=datetime.combine(upload_date, datetime.min.time()),
                description=f"{rule.description} (Bulk Provisioned)",
                user=rule.user,
                expense_type=rule.expense_type
            )
            db_exp = crud.create_expense(db, expense_in)
            inserted.append(db_exp)
            
    month_name = datetime(2026, target_month, 1).strftime('%B')
    
    html = f"""
    <div class="glass-card border border-brand-500/30 bg-brand-500/5 rounded-2xl p-5 mb-6 animate-fade-in">
        <div class="flex items-center gap-3 text-brand-400 mb-3 font-semibold">
            <i class="fa-solid fa-circle-check text-lg"></i>
            <span>Bulk Provisioning Completed!</span>
        </div>
    """
    
    if inserted:
        html += f"""
        <p class="text-xs text-slate-300 mb-3">Batch uploaded <strong>{len(inserted)}</strong> expense entry(ies) for {month_name} {target_year}:</p>
        <ul class="space-y-1 text-xs font-mono text-slate-400 list-disc list-inside">
        """
        for exp in inserted:
            html += f"<li>{exp.date.strftime('%Y-%m-%d')} : {exp.description} ({exp.user}) - £{abs(exp.amount):.2f}</li>"
        html += "</ul>"
    else:
        html += """
        <p class="text-xs text-rose-400">No items were selected or processed. Adjust rules and try again.</p>
        """
        
    html += "</div>"
    return html

# --- ADMIN SETTINGS RULES CRUD ---

@app.get("/admin-settings/rules/{rule_id}", response_class=HTMLResponse)
async def get_rule_row(request: Request, rule_id: int, db: Session = Depends(get_db)):
    rule = crud.get_scheduled_rule(db, rule_id)
    return templates.TemplateResponse(request=request, name="partials/rule_row.html", context={"rule": rule})

@app.get("/admin-settings/rules/new", response_class=HTMLResponse)
async def new_rule_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="partials/rule_form.html",
        context={
            "rule": None
        }
    )

@app.post("/admin-settings/rules/new", response_class=HTMLResponse)
async def create_rule_endpoint(
    request: Request,
    description: str = Form(...),
    rule_type: str = Form(...),
    day_of_month: int = Form(...),
    amount: float = Form(...),
    user: str = Form(...),
    expense_type: Optional[int] = Form(None),
    is_active: bool = Form(False),
    db: Session = Depends(get_db)
):
    # Form checkbox comes as 'true' or is absent. FastAPI Form binds automatically
    # but we can parse it from raw form data to be safe:
    form_data = await request.form()
    active_val = form_data.get("is_active") == "true"
    
    rule_in = ScheduledRuleCreate(
        description=description,
        rule_type=rule_type,
        day_of_month=day_of_month,
        amount=amount,
        user=user,
        expense_type=expense_type,
        is_active=active_val
    )
    rule = crud.create_scheduled_rule(db, rule_in)
    return templates.TemplateResponse(request=request, name="partials/rule_row.html", context={"rule": rule})

@app.get("/admin-settings/rules/{rule_id}/edit", response_class=HTMLResponse)
async def edit_rule_form(request: Request, rule_id: int, db: Session = Depends(get_db)):
    rule = crud.get_scheduled_rule(db, rule_id)
    return templates.TemplateResponse(request=request, name="partials/rule_form.html", context={"rule": rule})

@app.post("/admin-settings/rules/{rule_id}/edit", response_class=HTMLResponse)
async def update_rule_endpoint(
    request: Request,
    rule_id: int,
    description: str = Form(...),
    rule_type: str = Form(...),
    day_of_month: int = Form(...),
    amount: float = Form(...),
    user: str = Form(...),
    expense_type: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    form_data = await request.form()
    active_val = form_data.get("is_active") == "true"
    
    rule_in = ScheduledRuleUpdate(
        description=description,
        rule_type=rule_type,
        day_of_month=day_of_month,
        amount=amount,
        user=user,
        expense_type=expense_type,
        is_active=active_val
    )
    rule = crud.update_scheduled_rule(db, rule_id, rule_in)
    return templates.TemplateResponse(request=request, name="partials/rule_row.html", context={"rule": rule})

@app.delete("/admin-settings/rules/{rule_id}", response_class=HTMLResponse)
async def delete_rule_endpoint(rule_id: int, db: Session = Depends(get_db)):
    crud.delete_scheduled_rule(db, rule_id)
    return Response(status_code=200)

# Simulate scheduler runner manually from settings UI
@app.post("/admin-settings/run-scheduler", response_class=HTMLResponse)
async def simulate_scheduler(request: Request, db: Session = Depends(get_db)):
    # Run the modular scheduled insertions task for today
    inserted = process_scheduled_insertions(db)
    
    html = f"""
    <div class="glass-card border border-emerald-500/30 bg-emerald-500/5 rounded-2xl p-5 mb-6 animate-fade-in">
        <div class="flex items-center gap-3 text-emerald-400 mb-3 font-semibold">
            <i class="fa-solid fa-circle-check text-lg"></i>
            <span>Scheduler Run Completed Successfully!</span>
        </div>
    """
    
    if inserted:
        html += f"""
        <p class="text-xs text-slate-300 mb-3">Processed and inserted <strong>{len(inserted)}</strong> automated expense(s) for today ({date.today().strftime('%Y-%m-%d')}):</p>
        <ul class="space-y-1 text-xs font-mono text-slate-400 list-disc list-inside">
        """
        for exp in inserted:
            html += f"<li>{exp.date.strftime('%Y-%m-%d')} : {exp.description} ({exp.user}) - £{abs(exp.amount):.2f}</li>"
        html += "</ul>"
    else:
        html += """
        <p class="text-xs text-slate-400">All scheduled rules are already up-to-date for the current month. No new expenses were inserted.</p>
        """
        
    html += "</div>"
    return html
