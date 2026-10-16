from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class MonthlyFundCreate(BaseModel):
    hostel_id: int
    month: str = Field(..., description="e.g. 'October'")
    year: int = Field(..., ge=2000, le=2100, description="e.g. 2026")
    budget_holder_id: int = Field(..., description="User ID of the selected budget holder")
    per_student_contribution: Optional[float] = Field(None, gt=0, description="Optional default contribution per student")
    total_budget: Optional[float] = Field(0.0, ge=0, description="Initial total budget")


class MonthlyFundUpdate(BaseModel):
    status: Optional[str] = Field(None, description="'ACTIVE' or 'CLOSED'")
    budget_holder_id: Optional[int] = None


class MonthlyFundResponse(BaseModel):
    id: int
    hostel_id: int
    month: str
    year: int
    budget_holder_id: int
    budget_holder_name: Optional[str] = None
    total_budget: float
    current_balance: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
