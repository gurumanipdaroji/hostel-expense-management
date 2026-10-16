from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.hostel import Hostel, HostelMember
from app.models.monthly_fund import MonthlyFund
from app.models.contribution import Contribution
from app.schemas.hostel import HostelMemberAdd, HostelMemberResponse
from app.schemas.user import StudentCreate, StudentUpdateName, StudentResponse
from app.utils.auth import get_current_user, get_password_hash

router = APIRouter(tags=["Members"])


@router.post(
    "/hostels/{hostel_id}/students",
    response_model=HostelMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new student with full details to the hostel"
)
def create_and_add_student(
    hostel_id: int,
    student_in: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new student account with Name, USN / Student ID, Email, and Department,
    and immediately enrolls them as a member of the specified hostel.
    """
    # 1. Verify Hostel
    hostel = db.query(Hostel).filter(Hostel.id == hostel_id).first()
    if not hostel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hostel not found")

    cleaned_email = student_in.email.strip().lower()
    cleaned_usn = student_in.usn.strip().upper()
    cleaned_name = student_in.name.strip()
    cleaned_dept = student_in.department.strip()

    # 2. Check for duplicate email
    if db.query(User).filter(User.email == cleaned_email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A student with this email is already registered"
        )

    # 3. Check for duplicate Student ID / USN
    if db.query(User).filter(User.usn == cleaned_usn).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student ID / USN '{cleaned_usn}' already exists"
        )

    # 4. Create User permanently in database
    hashed_password = get_password_hash(student_in.password or "password123")
    new_user = User(
        name=cleaned_name,
        usn=cleaned_usn,
        email=cleaned_email,
        department=cleaned_dept,
        password_hash=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 5. Enroll in Hostel
    new_member = HostelMember(
        hostel_id=hostel_id,
        user_id=new_user.id,
        role=student_in.role.upper() if student_in.role else "MEMBER"
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    # 6. If an active monthly fund exists, enroll student in contributions
    active_funds = (
        db.query(MonthlyFund)
        .filter(MonthlyFund.hostel_id == hostel_id, MonthlyFund.status == "ACTIVE")
        .all()
    )
    for fund in active_funds:
        existing_contrib = (
            db.query(Contribution)
            .filter(Contribution.monthly_fund_id == fund.id)
            .first()
        )
        default_amt = existing_contrib.amount if existing_contrib else 2000.0
        contrib = Contribution(
            monthly_fund_id=fund.id,
            student_id=new_user.id,
            amount=default_amt,
            paid=True,
            payment_date=datetime.utcnow()
        )
        db.add(contrib)
    db.commit()

    return {
        "id": new_member.id,
        "hostel_id": new_member.hostel_id,
        "user_id": new_user.id,
        "user_name": new_user.name,
        "user_email": new_user.email,
        "usn": new_user.usn,
        "department": new_user.department,
        "role": new_member.role,
        "joined_at": new_member.joined_at
    }


@router.post(
    "/hostels/{hostel_id}/members", 
    response_model=HostelMemberResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Add an existing student to a hostel by their email"
)
def add_hostel_member(
    hostel_id: int,
    member_in: HostelMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Adds an already-registered student to the hostel using their email address.
    """
    hostel = db.query(Hostel).filter(Hostel.id == hostel_id).first()
    if not hostel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hostel not found")

    user_to_add = db.query(User).filter(User.email == member_in.email.lower().strip()).first()
    if not user_to_add:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student with this email not found. Please add them as a new student first."
        )

    existing_member = (
        db.query(HostelMember)
        .filter(HostelMember.hostel_id == hostel_id, HostelMember.user_id == user_to_add.id)
        .first()
    )
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already a member of this hostel"
        )

    new_member = HostelMember(
        hostel_id=hostel_id,
        user_id=user_to_add.id,
        role=member_in.role.upper() if member_in.role else "MEMBER"
    )
    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return {
        "id": new_member.id,
        "hostel_id": new_member.hostel_id,
        "user_id": user_to_add.id,
        "user_name": user_to_add.name,
        "user_email": user_to_add.email,
        "usn": user_to_add.usn,
        "department": user_to_add.department,
        "role": new_member.role,
        "joined_at": new_member.joined_at
    }


@router.get(
    "/hostels/{hostel_id}/members", 
    response_model=List[HostelMemberResponse],
    summary="Get all members of a hostel"
)
def list_hostel_members(
    hostel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all student members in the specified hostel with full student details.
    """
    hostel = db.query(Hostel).filter(Hostel.id == hostel_id).first()
    if not hostel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hostel not found")

    members = (
        db.query(HostelMember, User)
        .join(User, HostelMember.user_id == User.id)
        .filter(HostelMember.hostel_id == hostel_id)
        .order_by(HostelMember.joined_at.asc())
        .all()
    )

    return [
        {
            "id": m.HostelMember.id,
            "hostel_id": m.HostelMember.hostel_id,
            "user_id": m.User.id,
            "user_name": m.User.name,
            "user_email": m.User.email,
            "usn": m.User.usn,
            "department": m.User.department,
            "role": m.HostelMember.role,
            "joined_at": m.HostelMember.joined_at
        }
        for m in members
    ]


@router.put(
    "/students/{student_id}/name",
    response_model=StudentResponse,
    summary="Change only a student's name"
)
def update_student_name(
    student_id: int,
    update_in: StudentUpdateName,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates ONLY the student's name.
    USN, email, department, and other student information remain strictly unchanged.
    """
    user = db.query(User).filter(User.id == student_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    new_name = update_in.name.strip()
    if len(new_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Student name must be at least 2 characters long"
        )

    # Change only student's name - preserve USN, email, department, password, etc.
    user.name = new_name
    db.commit()
    db.refresh(user)

    return user


@router.put(
    "/hostels/{hostel_id}/members/{user_id}/name",
    response_model=StudentResponse,
    summary="Change a student member's name within hostel context"
)
def update_hostel_member_name(
    hostel_id: int,
    user_id: int,
    update_in: StudentUpdateName,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Convenience route to change student name within hostel context.
    """
    return update_student_name(student_id=user_id, update_in=update_in, db=db, current_user=current_user)


@router.get(
    "/students/{student_id}",
    response_model=StudentResponse,
    summary="Get single student details"
)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves details of a student by ID.
    """
    user = db.query(User).filter(User.id == student_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return user


@router.delete(
    "/hostels/{hostel_id}/members/{user_id}", 
    status_code=status.HTTP_200_OK,
    summary="Remove a member from the hostel"
)
def remove_hostel_member(
    hostel_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Removes a member from the hostel.
    """
    member = (
        db.query(HostelMember)
        .filter(HostelMember.hostel_id == hostel_id, HostelMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Student is not a member of this hostel"
        )

    db.delete(member)
    db.commit()
    return {"message": "Member removed successfully"}
