from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    monthly_fund_id = Column(Integer, ForeignKey("monthly_funds.id"), nullable=False)
    paid_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # Food, Groceries, Electricity, Gas, Water, Cleaning, Maintenance, Other
    amount = Column(Float, nullable=False)
    payment_source = Column(String(30), nullable=False)  # "COMMON_MONEY" or "PERSONAL_MONEY"
    expense_date = Column(Date, nullable=False, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    monthly_fund = relationship("MonthlyFund", back_populates="expenses")
    payer = relationship("User", back_populates="expenses_paid", foreign_keys=[paid_by])
