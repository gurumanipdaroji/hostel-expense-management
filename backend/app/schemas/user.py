from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of student")
    email: EmailStr = Field(..., description="Student email address")
    password: str = Field(..., min_length=4, max_length=100, description="Account password")
    usn: Optional[str] = Field(None, min_length=2, max_length=50, description="Student ID / USN")
    department: Optional[str] = Field(None, min_length=2, max_length=100, description="Department / Class / Section")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    usn: Optional[str] = None
    email: str
    department: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class StudentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of student")
    usn: str = Field(..., min_length=2, max_length=50, description="Student ID / USN")
    email: EmailStr = Field(..., description="Student email address")
    department: str = Field(..., min_length=2, max_length=100, description="Department / Class / Section")
    role: Optional[str] = Field(default="MEMBER", description="Role: 'ADMIN' or 'MEMBER'")
    password: Optional[str] = Field(default="password123", min_length=4, max_length=100, description="Account password")


class StudentUpdateName(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="New full name of student")


class StudentResponse(BaseModel):
    id: int
    name: str
    usn: Optional[str] = None
    email: str
    department: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
