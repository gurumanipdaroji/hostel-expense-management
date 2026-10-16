from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Contribution(Base):
    __tablename__ = "contributions"

    id = Column(Integer, primary_key=True, index=True)
    monthly_fund_id = Column(Integer, ForeignKey("monthly_funds.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    paid = Column(Boolean, default=False, nullable=False)
    payment_date = Column(DateTime, nullable=True)

    # Relationships
    monthly_fund = relationship("MonthlyFund", back_populates="contributions")
    student = relationship("User", back_populates="contributions")
