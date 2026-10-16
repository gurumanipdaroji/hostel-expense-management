from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.hostel import HostelMember
from app.models.monthly_fund import MonthlyFund
from app.models.contribution import Contribution
from app.models.expense import Expense
from app.utils.auth import get_current_user

router = APIRouter(tags=["Dashboard"])


@router.get(
    "/dashboard/{monthly_fund_id}",
    summary="Get complete dashboard statistics and overview for a monthly fund"
)
def get_dashboard_summary(
    monthly_fund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns high-level metric cards, recent expenses, member contributions,
    and budget holder information for the dashboard.
    """
    fund = db.query(MonthlyFund).filter(MonthlyFund.id == monthly_fund_id).first()
    if not fund:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Monthly fund not found")

    # 1. Budget holder info
    budget_holder = db.query(User).filter(User.id == fund.budget_holder_id).first()

    # 2. Expenses breakdown
    expenses = db.query(Expense).filter(Expense.monthly_fund_id == fund.id).all()
    common_spent = sum(e.amount for e in expenses if e.payment_source == "COMMON_MONEY")
    personal_spent = sum(e.amount for e in expenses if e.payment_source == "PERSONAL_MONEY")

    # 3. Members of the hostel
    memberships = (
        db.query(HostelMember, User)
        .join(User, HostelMember.user_id == User.id)
        .filter(HostelMember.hostel_id == fund.hostel_id)
        .all()
    )

    # 4. Contributions status
    contributions = db.query(Contribution).filter(Contribution.monthly_fund_id == fund.id).all()
    contrib_map = {c.student_id: c for c in contributions}

    members_summary = []
    paid_members_count = 0
    for m, u in memberships:
        c = contrib_map.get(u.id)
        is_paid = c.paid if c else False
        amount = c.amount if c else 0.0
        if is_paid:
            paid_members_count += 1
        members_summary.append({
            "student_id": u.id,
            "name": u.name,
            "usn": u.usn,
            "email": u.email,
            "department": u.department,
            "role": m.role,
            "is_budget_holder": (u.id == fund.budget_holder_id),
            "contribution_amount": amount,
            "contribution_paid": is_paid
        })

    # 5. Recent expenses (top 5 latest)
    recent_expenses = (
        db.query(Expense, User)
        .join(User, Expense.paid_by == User.id)
        .filter(Expense.monthly_fund_id == fund.id)
        .order_by(Expense.expense_date.desc(), Expense.id.desc())
        .limit(6)
        .all()
    )

    recent_expenses_list = [
        {
            "id": item.Expense.id,
            "description": item.Expense.description,
            "category": item.Expense.category,
            "amount": item.Expense.amount,
            "payment_source": item.Expense.payment_source,
            "expense_date": item.Expense.expense_date,
            "paid_by_name": item.User.name
        }
        for item in recent_expenses
    ]

    return {
        "monthly_fund_id": fund.id,
        "hostel_id": fund.hostel_id,
        "month": fund.month,
        "year": fund.year,
        "status": fund.status,
        "budget_holder": {
            "id": budget_holder.id if budget_holder else None,
            "name": budget_holder.name if budget_holder else "Unknown",
            "email": budget_holder.email if budget_holder else ""
        },
        "cards": {
            "monthly_budget": round(fund.total_budget, 2),
            "current_common_balance": round(fund.current_balance, 2),
            "common_money_spent": round(common_spent, 2),
            "personal_expenses": round(personal_spent, 2),
            "settlement_pending": round(personal_spent, 2),
            "number_of_members": len(memberships),
            "members_paid_count": paid_members_count
        },
        "recent_expenses": recent_expenses_list,
        "members": members_summary
    }
