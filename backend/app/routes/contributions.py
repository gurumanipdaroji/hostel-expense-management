from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.hostel import HostelMember
from app.models.monthly_fund import MonthlyFund
from app.models.contribution import Contribution
from app.schemas.contribution import (
    ContributionCreate, ContributionUpdate, ContributionResponse
)
from app.utils.auth import get_current_user

router = APIRouter(tags=["Contributions"])


def recalculate_fund_budget(db: Session, monthly_fund: MonthlyFund):
    """
    Recalculates the monthly fund's starting total budget and current balance
    based on all recorded paid contributions, minus common money expenses.
    """
    from app.models.expense import Expense

    paid_contributions_sum = (
        db.query(Contribution)
        .filter(Contribution.monthly_fund_id == monthly_fund.id, Contribution.paid == True)
        .all()
    )
    total_paid = sum(c.amount for c in paid_contributions_sum)
    
    # Total common money expenses spent so far
    common_expenses = (
        db.query(Expense)
        .filter(Expense.monthly_fund_id == monthly_fund.id, Expense.payment_source == "COMMON_MONEY")
        .all()
    )
    total_spent = sum(e.amount for e in common_expenses)

    monthly_fund.total_budget = round(total_paid, 2)
    monthly_fund.current_balance = round(total_paid - total_spent, 2)
    db.commit()


@router.post(
    "/contributions", 
    response_model=ContributionResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Record a member's monthly contribution"
)
def create_contribution(
    contrib_in: ContributionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Records an individual student's contribution for a monthly fund.
    """
    if contrib_in.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contribution amount must be greater than zero"
        )

    fund = db.query(MonthlyFund).filter(MonthlyFund.id == contrib_in.monthly_fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly fund not found")

    if fund.status == "CLOSED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Monthly fund is closed")

    # Check member is in the hostel
    member = (
        db.query(HostelMember)
        .filter(HostelMember.hostel_id == fund.hostel_id, HostelMember.user_id == contrib_in.student_id)
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not a member of this hostel"
        )

    # Check if contribution already exists for this student
    existing = (
        db.query(Contribution)
        .filter(
            Contribution.monthly_fund_id == fund.id, 
            Contribution.student_id == contrib_in.student_id
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Monthly contribution already recorded"
        )

    payment_dt = contrib_in.payment_date or (datetime.utcnow() if contrib_in.paid else None)

    contribution = Contribution(
        monthly_fund_id=fund.id,
        student_id=contrib_in.student_id,
        amount=round(contrib_in.amount, 2),
        paid=contrib_in.paid,
        payment_date=payment_dt
    )
    db.add(contribution)
    db.commit()
    db.refresh(contribution)

    # Sync fund balance
    recalculate_fund_budget(db, fund)

    student = db.query(User).filter(User.id == contribution.student_id).first()
    return {
        "id": contribution.id,
        "monthly_fund_id": contribution.monthly_fund_id,
        "student_id": contribution.student_id,
        "student_name": student.name if student else None,
        "student_email": student.email if student else None,
        "amount": contribution.amount,
        "paid": contribution.paid,
        "payment_date": contribution.payment_date
    }


@router.get(
    "/monthly-funds/{fund_id}/contributions", 
    response_model=List[ContributionResponse],
    summary="List all contributions for a monthly fund"
)
def get_fund_contributions(
    fund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all member contributions for the monthly fund.
    """
    contributions = (
        db.query(Contribution, User)
        .join(User, Contribution.student_id == User.id)
        .filter(Contribution.monthly_fund_id == fund_id)
        .all()
    )

    return [
        {
            "id": c.Contribution.id,
            "monthly_fund_id": c.Contribution.monthly_fund_id,
            "student_id": c.User.id,
            "student_name": c.User.name,
            "student_email": c.User.email,
            "amount": c.Contribution.amount,
            "paid": c.Contribution.paid,
            "payment_date": c.Contribution.payment_date
        }
        for c in contributions
    ]


@router.put(
    "/contributions/{id}", 
    response_model=ContributionResponse,
    summary="Update a contribution's paid status or amount"
)
def update_contribution(
    id: int,
    contrib_update: ContributionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Updates whether a student has paid their monthly contribution or modifies the amount.
    """
    contribution = db.query(Contribution).filter(Contribution.id == id).first()
    if not contribution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution not found")

    fund = db.query(MonthlyFund).filter(MonthlyFund.id == contribution.monthly_fund_id).first()
    if fund and fund.status == "CLOSED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Monthly fund is closed")

    if contrib_update.amount is not None:
        if contrib_update.amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expense amount must be greater than zero"
            )
        contribution.amount = round(contrib_update.amount, 2)

    if contrib_update.paid is not None:
        contribution.paid = contrib_update.paid
        if contribution.paid and not contribution.payment_date:
            contribution.payment_date = datetime.utcnow()
        elif not contribution.paid:
            contribution.payment_date = None

    db.commit()
    db.refresh(contribution)

    if fund:
        recalculate_fund_budget(db, fund)

    student = db.query(User).filter(User.id == contribution.student_id).first()
    return {
        "id": contribution.id,
        "monthly_fund_id": contribution.monthly_fund_id,
        "student_id": contribution.student_id,
        "student_name": student.name if student else None,
        "student_email": student.email if student else None,
        "amount": contribution.amount,
        "paid": contribution.paid,
        "payment_date": contribution.payment_date
    }
