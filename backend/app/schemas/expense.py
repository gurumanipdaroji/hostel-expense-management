from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional


class ExpenseCreate(BaseModel):
    monthly_fund_id: int
    paid_by: int
    description: str = Field(..., min_length=2, max_length=255)
    category: str = Field(..., description="Food, Groceries, Electricity, Gas, Water, Cleaning, Maintenance, Other")
    amount: float = Field(..., gt=0, description="Expense amount must be greater than zero")
    payment_source: str = Field(..., description="'COMMON_MONEY' or 'PERSONAL_MONEY'")
    expense_date: Optional[date] = Field(default_factory=date.today)

    @field_validator("payment_source")
    @classmethod
    def validate_payment_source(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if cleaned not in ["COMMON_MONEY", "PERSONAL_MONEY"]:
            raise ValueError("payment_source must be either 'COMMON_MONEY' or 'PERSONAL_MONEY'")
        return cleaned


class ExpenseResponse(BaseModel):
    id: int
    monthly_fund_id: int
    paid_by: int
    payer_name: Optional[str] = None
    description: str
    category: str
    amount: float
    payment_source: str
    expense_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
