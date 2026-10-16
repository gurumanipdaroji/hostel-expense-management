from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.hostel import HostelMember
from app.models.monthly_fund import MonthlyFund
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseResponse
from app.utils.auth import get_current_user

router = APIRouter(tags=["Expenses"])


@router.post(
    "/expenses", 
    response_model=ExpenseResponse, 
    status_code=status.HTTP_201_CREATED,
    summary="Record a new hostel expense"
)
def create_expense(
    expense_in: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Records an expense using either COMMON_MONEY or PERSONAL_MONEY.
    
    Business Logic:
    - If COMMON_MONEY:
        Verifies amount <= current_balance.
        If valid: deducts amount from monthly_fund.current_balance.
        If insufficient: rejects with 400 'Insufficient common balance'.
    - If PERSONAL_MONEY:
        Does NOT alter common balance. Contributes to monthly settlement.
    """
    if expense_in.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Expense amount must be greater than zero"
        )

    # 1. Verify Monthly Fund
    fund = db.query(MonthlyFund).filter(MonthlyFund.id == expense_in.monthly_fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly fund not found")

    if fund.status == "CLOSED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Monthly fund is closed")

    # 2. Verify Payer is a member of this hostel
    member = (
        db.query(HostelMember)
        .filter(HostelMember.hostel_id == fund.hostel_id, HostelMember.user_id == expense_in.paid_by)
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is not a member of this hostel"
        )

    # 3. Handle Payment Source Logic
    if expense_in.payment_source == "COMMON_MONEY":
        if expense_in.amount > fund.current_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient common balance. Current balance is ₹{fund.current_balance:.2f}, but expense is ₹{expense_in.amount:.2f}"
            )
        fund.current_balance = round(fund.current_balance - expense_in.amount, 2)
    elif expense_in.payment_source == "PERSONAL_MONEY":
        # Personal money does not affect current_balance
        pass

    # 4. Save Expense
    expense = Expense(
        monthly_fund_id=fund.id,
        paid_by=expense_in.paid_by,
        description=expense_in.description.strip(),
        category=expense_in.category.strip(),
        amount=round(expense_in.amount, 2),
        payment_source=expense_in.payment_source,
        expense_date=expense_in.expense_date or date.today()
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    payer = db.query(User).filter(User.id == expense.paid_by).first()

    return {
        "id": expense.id,
        "monthly_fund_id": expense.monthly_fund_id,
        "paid_by": expense.paid_by,
        "payer_name": payer.name if payer else None,
        "description": expense.description,
        "category": expense.category,
        "amount": expense.amount,
        "payment_source": expense.payment_source,
        "expense_date": expense.expense_date,
        "created_at": expense.created_at
    }


@router.get(
    "/monthly-funds/{fund_id}/expenses", 
    response_model=List[ExpenseResponse],
    summary="List all expenses for a monthly fund with optional filters"
)
def get_fund_expenses(
    fund_id: int,
    category: Optional[str] = Query(None, description="Filter by category e.g. Food, Groceries"),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    payment_source: Optional[str] = Query(None, description="COMMON_MONEY or PERSONAL_MONEY"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns expenses for a monthly fund, with optional filters for category, student, and payment source.
    """
    query = (
        db.query(Expense, User)
        .join(User, Expense.paid_by == User.id)
        .filter(Expense.monthly_fund_id == fund_id)
    )

    if category:
        query = query.filter(Expense.category.ilike(f"%{category.strip()}%"))

    if student_id:
        query = query.filter(Expense.paid_by == student_id)

    if payment_source:
        query = query.filter(Expense.payment_source == payment_source.strip().upper())

    results = query.order_by(Expense.expense_date.desc(), Expense.id.desc()).all()

    return [
        {
            "id": item.Expense.id,
            "monthly_fund_id": item.Expense.monthly_fund_id,
            "paid_by": item.User.id,
            "payer_name": item.User.name,
            "description": item.Expense.description,
            "category": item.Expense.category,
            "amount": item.Expense.amount,
            "payment_source": item.Expense.payment_source,
            "expense_date": item.Expense.expense_date,
            "created_at": item.Expense.created_at
        }
        for item in results
    ]


@router.get(
    "/expenses/{id}", 
    response_model=ExpenseResponse,
    summary="Get single expense details by ID"
)
def get_expense(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a single expense by ID.
    """
    expense = db.query(Expense).filter(Expense.id == id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    payer = db.query(User).filter(User.id == expense.paid_by).first()

    return {
        "id": expense.id,
        "monthly_fund_id": expense.monthly_fund_id,
        "paid_by": expense.paid_by,
        "payer_name": payer.name if payer else None,
        "description": expense.description,
        "category": expense.category,
        "amount": expense.amount,
        "payment_source": expense.payment_source,
        "expense_date": expense.expense_date,
        "created_at": expense.created_at
    }


@router.delete(
    "/expenses/{id}", 
    status_code=status.HTTP_200_OK,
    summary="Delete an expense record"
)
def delete_expense(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes an expense. If it was COMMON_MONEY, restores the deducted amount back to the monthly fund balance.
    """
    expense = db.query(Expense).filter(Expense.id == id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    fund = db.query(MonthlyFund).filter(MonthlyFund.id == expense.monthly_fund_id).first()
    if fund and fund.status == "CLOSED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Monthly fund is closed")

    # If it was common money, restore the balance
    if fund and expense.payment_source == "COMMON_MONEY":
        fund.current_balance = round(fund.current_balance + expense.amount, 2)

    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}
