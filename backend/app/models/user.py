from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    usn = Column(String(50), unique=True, index=True, nullable=True)  # Student ID / USN
    email = Column(String(120), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=True)                  # Department / Class / Section
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    created_hostels = relationship("Hostel", back_populates="creator", foreign_keys="Hostel.created_by")
    memberships = relationship("HostelMember", back_populates="user", cascade="all, delete-orphan")
    contributions = relationship("Contribution", back_populates="student", cascade="all, delete-orphan")
    expenses_paid = relationship("Expense", back_populates="payer", foreign_keys="Expense.paid_by")
