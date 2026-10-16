from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class HostelCreate(BaseModel):
    hostel_name: str = Field(..., min_length=2, max_length=150, description="Name of the hostel")


class HostelResponse(BaseModel):
    id: int
    hostel_name: str
    created_by: int
    created_at: datetime
    member_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class HostelMemberAdd(BaseModel):
    email: str = Field(..., description="Email address of the student to add")
    role: str = Field(default="MEMBER", description="Role: 'ADMIN' or 'MEMBER'")


class HostelMemberResponse(BaseModel):
    id: int
    hostel_id: int
    user_id: int
    user_name: str
    user_email: str
    usn: Optional[str] = None
    department: Optional[str] = None
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
