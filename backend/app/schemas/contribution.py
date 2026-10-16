from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ContributionCreate(BaseModel):
    monthly_fund_id: int
    student_id: int
    amount: float = Field(..., gt=0, description="Contribution amount must be greater than zero")
    paid: bool = Field(default=True, description="Whether the contribution has been paid")
    payment_date: Optional[datetime] = None


class ContributionUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    paid: Optional[bool] = None


class ContributionResponse(BaseModel):
    id: int
    monthly_fund_id: int
    student_id: int
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    amount: float
    paid: bool
    payment_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
