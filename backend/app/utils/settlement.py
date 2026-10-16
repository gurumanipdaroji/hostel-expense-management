from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.monthly_fund import MonthlyFund
from app.models.expense import Expense
from app.models.hostel import HostelMember
from app.models.user import User


def calculate_settlement(db: Session, monthly_fund: MonthlyFund) -> Dict[str, Any]:
    """
    Calculates the complete monthly settlement breakdown.
    
    Business Rules:
    1. Starting Budget = fund.total_budget (e.g. ₹10,000)
    2. Total COMMON_MONEY expenses reduce the common balance directly.
    3. Current Common Balance = Starting Budget - Total COMMON_MONEY expenses.
    4. PERSONAL_MONEY expenses DO NOT reduce the common balance during the month.
    5. Each student's PERSONAL_MONEY expenses create an amount owed to that student
       (to be reimbursed by the budget holder from the remaining common fund).
    6. Total Settlement Amount = Sum of all PERSONAL_MONEY expenses.
    """
    # 1. Fetch all expenses for this monthly fund
    expenses = db.query(Expense).filter(Expense.monthly_fund_id == monthly_fund.id).all()

    total_common_expenses = 0.0
    total_personal_expenses = 0.0
    student_personal_map: Dict[int, float] = {}

    for exp in expenses:
        if exp.payment_source == "COMMON_MONEY":
            total_common_expenses += exp.amount
        elif exp.payment_source == "PERSONAL_MONEY":
            total_personal_expenses += exp.amount
            student_personal_map[exp.paid_by] = student_personal_map.get(exp.paid_by, 0.0) + exp.amount

    # 2. Get all members of the hostel for complete visibility
    members = (
        db.query(HostelMember)
        .filter(HostelMember.hostel_id == monthly_fund.hostel_id)
        .all()
    )

    # 3. Build per-student settlement details
    students_settlement: List[Dict[str, Any]] = []
    
    # Track member IDs already processed
    processed_ids = set()

    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            personal_spent = student_personal_map.get(user.id, 0.0)
            students_settlement.append({
                "student_id": user.id,
                "student_name": user.name,
                "usn": user.usn,
                "email": user.email,
                "role": m.role,
                "is_budget_holder": (user.id == monthly_fund.budget_holder_id),
                "personal_expenses": round(personal_spent, 2),
                "amount_to_receive": round(personal_spent, 2)
            })
            processed_ids.add(user.id)

    # Include any student who paid personal expenses but might not have a current member record
    for student_id, spent in student_personal_map.items():
        if student_id not in processed_ids:
            user = db.query(User).filter(User.id == student_id).first()
            if user:
                students_settlement.append({
                    "student_id": user.id,
                    "student_name": user.name,
                    "email": user.email,
                    "role": "MEMBER",
                    "is_budget_holder": (user.id == monthly_fund.budget_holder_id),
                    "personal_expenses": round(spent, 2),
                    "amount_to_receive": round(spent, 2)
                })

    # Sort students so those owed money appear first, then by name
    students_settlement.sort(key=lambda s: (-s["amount_to_receive"], s["student_name"]))

    # Current common balance (verified against database record)
    calculated_common_balance = monthly_fund.total_budget - total_common_expenses

    # Budget holder info
    budget_holder = db.query(User).filter(User.id == monthly_fund.budget_holder_id).first()
    budget_holder_name = budget_holder.name if budget_holder else "Unknown"

    # Remaining common balance after settling personal expenses
    remaining_after_settlement = calculated_common_balance - total_personal_expenses

    return {
        "monthly_fund_id": monthly_fund.id,
        "month": monthly_fund.month,
        "year": monthly_fund.year,
        "status": monthly_fund.status,
        "budget_holder_id": monthly_fund.budget_holder_id,
        "budget_holder_name": budget_holder_name,
        "starting_budget": round(monthly_fund.total_budget, 2),
        "total_common_expenses": round(total_common_expenses, 2),
        "current_common_balance": round(calculated_common_balance, 2),
        "total_personal_expenses": round(total_personal_expenses, 2),
        "total_settlement_amount": round(total_personal_expenses, 2),
        "remaining_after_settlement": round(remaining_after_settlement, 2),
        "students": students_settlement
    }
