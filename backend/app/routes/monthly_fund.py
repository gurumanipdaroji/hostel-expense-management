from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.hostel import Hostel, HostelMember
from app.models.monthly_fund import MonthlyFund
from app.models.contribution import Contribution
from app.schemas.monthly_fund import (
    MonthlyFundCreate, MonthlyFundResponse, MonthlyFundUpdate
)
from app.utils.auth import get_current_user

router = APIRouter(tags=["Monthly Funds"])


@router.post(
    "/monthly-funds", 
    response_model=MonthlyFundResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Create a new monthly fund for a hostel"
)
def create_monthly_fund(
    fund_in: MonthlyFundCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Creates a new monthly fund with a selected budget holder.
    Optionally initializes contributions for all hostel members.
    """
    # 1. Check hostel exists
    hostel = db.query(Hostel).filter(Hostel.id == fund_in.hostel_id).first()
    if not hostel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hostel not found")

    # 2. Check if budget holder is a member of this hostel
    holder_member = (
        db.query(HostelMember)
        .filter(HostelMember.hostel_id == fund_in.hostel_id, HostelMember.user_id == fund_in.budget_holder_id)
        .first()
    )
    if not holder_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not a member of this hostel"
        )

    # 3. Check if fund already exists for this month & year
    existing_fund = (
        db.query(MonthlyFund)
        .filter(
            MonthlyFund.hostel_id == fund_in.hostel_id,
            MonthlyFund.month.ilike(fund_in.month.strip()),
            MonthlyFund.year == fund_in.year
        )
        .first()
    )
    if existing_fund:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A fund for {fund_in.month} {fund_in.year} already exists for this hostel"
        )

    # 4. Calculate total budget if per_student_contribution is supplied
    members = db.query(HostelMember).filter(HostelMember.hostel_id == fund_in.hostel_id).all()
    calculated_total = fund_in.total_budget or 0.0

    if fund_in.per_student_contribution and fund_in.per_student_contribution > 0:
        calculated_total = fund_in.per_student_contribution * len(members)

    # 5. Create MonthlyFund record
    monthly_fund = MonthlyFund(
        hostel_id=fund_in.hostel_id,
        month=fund_in.month.strip().capitalize(),
        year=fund_in.year,
        budget_holder_id=fund_in.budget_holder_id,
        total_budget=round(calculated_total, 2),
        current_balance=round(calculated_total, 2),
        status="ACTIVE"
    )
    db.add(monthly_fund)
    db.commit()
    db.refresh(monthly_fund)

    # 6. Auto-generate contribution records for each member if per_student_contribution given
    if fund_in.per_student_contribution and fund_in.per_student_contribution > 0:
        for m in members:
            contrib = Contribution(
                monthly_fund_id=monthly_fund.id,
                student_id=m.user_id,
                amount=fund_in.per_student_contribution,
                paid=True,  # Default to collected at start of month
                payment_date=datetime.utcnow()
            )
            db.add(contrib)
        db.commit()

    holder_user = db.query(User).filter(User.id == monthly_fund.budget_holder_id).first()

    return {
        "id": monthly_fund.id,
        "hostel_id": monthly_fund.hostel_id,
        "month": monthly_fund.month,
        "year": monthly_fund.year,
        "budget_holder_id": monthly_fund.budget_holder_id,
        "budget_holder_name": holder_user.name if holder_user else None,
        "total_budget": monthly_fund.total_budget,
        "current_balance": monthly_fund.current_balance,
        "status": monthly_fund.status,
        "created_at": monthly_fund.created_at
    }


@router.get(
    "/monthly-funds/{fund_id}", 
    response_model=MonthlyFundResponse,
    summary="Get details of a specific monthly fund"
)
def get_monthly_fund(
    fund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns monthly fund information by ID.
    """
    fund = db.query(MonthlyFund).filter(MonthlyFund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly fund not found")

    holder = db.query(User).filter(User.id == fund.budget_holder_id).first()

    return {
        "id": fund.id,
        "hostel_id": fund.hostel_id,
        "month": fund.month,
        "year": fund.year,
        "budget_holder_id": fund.budget_holder_id,
        "budget_holder_name": holder.name if holder else None,
        "total_budget": fund.total_budget,
        "current_balance": fund.current_balance,
        "status": fund.status,
        "created_at": fund.created_at
    }


@router.get(
    "/hostels/{hostel_id}/monthly-funds", 
    response_model=List[MonthlyFundResponse],
    summary="List all monthly funds for a specific hostel"
)
def get_hostel_monthly_funds(
    hostel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns all monthly funds for a hostel, newest first.
    """
    funds = (
        db.query(MonthlyFund)
        .filter(MonthlyFund.hostel_id == hostel_id)
        .order_by(MonthlyFund.year.desc(), MonthlyFund.id.desc())
        .all()
    )

    result = []
    for f in funds:
        holder = db.query(User).filter(User.id == f.budget_holder_id).first()
        result.append({
            "id": f.id,
            "hostel_id": f.hostel_id,
            "month": f.month,
            "year": f.year,
            "budget_holder_id": f.budget_holder_id,
            "budget_holder_name": holder.name if holder else None,
            "total_budget": f.total_budget,
            "current_balance": f.current_balance,
            "status": f.status,
            "created_at": f.created_at
        })
    return result


@router.put(
    "/monthly-funds/{fund_id}/status", 
    response_model=MonthlyFundResponse,
    summary="Update status of a monthly fund (ACTIVE / CLOSED)"
)
def update_monthly_fund_status(
    fund_id: int,
    update_in: MonthlyFundUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates the status (ACTIVE/CLOSED) of a monthly fund.
    """
    fund = db.query(MonthlyFund).filter(MonthlyFund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly fund not found")

    if update_in.status:
        cleaned_status = update_in.status.strip().upper()
        if cleaned_status not in ["ACTIVE", "CLOSED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Status must be either 'ACTIVE' or 'CLOSED'"
            )
        fund.status = cleaned_status

    if update_in.budget_holder_id:
        holder_user = db.query(User).filter(User.id == update_in.budget_holder_id).first()
        if not holder_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget holder user not found")
        fund.budget_holder_id = update_in.budget_holder_id

    db.commit()
    db.refresh(fund)
    holder = db.query(User).filter(User.id == fund.budget_holder_id).first()

    return {
        "id": fund.id,
        "hostel_id": fund.hostel_id,
        "month": fund.month,
        "year": fund.year,
        "budget_holder_id": fund.budget_holder_id,
        "budget_holder_name": holder.name if holder else None,
        "total_budget": fund.total_budget,
        "current_balance": fund.current_balance,
        "status": fund.status,
        "created_at": fund.created_at
    }
