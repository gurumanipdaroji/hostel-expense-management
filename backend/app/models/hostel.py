from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Hostel(Base):
    __tablename__ = "hostels"

    id = Column(Integer, primary_key=True, index=True)
    hostel_name = Column(String(150), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_hostels", foreign_keys=[created_by])
    members = relationship("HostelMember", back_populates="hostel", cascade="all, delete-orphan")
    monthly_funds = relationship("MonthlyFund", back_populates="hostel", cascade="all, delete-orphan")


class HostelMember(Base):
    __tablename__ = "hostel_members"

    id = Column(Integer, primary_key=True, index=True)
    hostel_id = Column(Integer, ForeignKey("hostels.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="MEMBER", nullable=False)  # "ADMIN" or "MEMBER"
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    hostel = relationship("Hostel", back_populates="members")
    user = relationship("User", back_populates="memberships")
