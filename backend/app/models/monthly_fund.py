from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class MonthlyFund(Base):
    __tablename__ = "monthly_funds"

    id = Column(Integer, primary_key=True, index=True)
    hostel_id = Column(Integer, ForeignKey("hostels.id"), nullable=False)
    month = Column(String(30), nullable=False)  # e.g., "October"
    year = Column(Integer, nullable=False)       # e.g., 2026
    budget_holder_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_budget = Column(Float, default=0.0, nullable=False)
    current_balance = Column(Float, default=0.0, nullable=False)
    status = Column(String(20), default="ACTIVE", nullable=False)  # "ACTIVE" or "CLOSED"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    hostel = relationship("Hostel", back_populates="monthly_funds")
    budget_holder = relationship("User", foreign_keys=[budget_holder_id])
    contributions = relationship("Contribution", back_populates="monthly_fund", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="monthly_fund", cascade="all, delete-orphan")
