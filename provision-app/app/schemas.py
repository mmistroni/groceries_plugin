from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional

class ExpenseBase(BaseModel):
    amount: float
    date: datetime
    description: str
    user: str
    expense_type: Optional[int] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    date: Optional[datetime] = None
    description: Optional[str] = None
    user: Optional[str] = None
    expense_type: Optional[int] = None

class ExpenseResponse(ExpenseBase):
    id: int

    class Config:
        from_attributes = True

class ScheduledRuleBase(BaseModel):
    description: str
    amount: float
    day_of_month: int = Field(..., ge=1, le=31)
    rule_type: str  # 'direct_debit' or 'lump_sum'
    expense_type: Optional[int] = None
    user: Optional[str] = "directdebit"
    is_active: Optional[bool] = True

class ScheduledRuleCreate(ScheduledRuleBase):
    pass

class ScheduledRuleUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[float] = None
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    rule_type: Optional[str] = None
    expense_type: Optional[int] = None
    user: Optional[str] = None
    is_active: Optional[bool] = None

class ScheduledRuleResponse(ScheduledRuleBase):
    id: int
    last_run: Optional[date] = None

    class Config:
        from_attributes = True
