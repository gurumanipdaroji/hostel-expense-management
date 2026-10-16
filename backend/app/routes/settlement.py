from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.monthly_fund import MonthlyFund
from app.utils.settlement import calculate_settlement
from app.utils.auth import get_current_user

router = APIRouter(tags=["Settlement"])


@router.get(
    "/settlement/{monthly_fund_id}",
    summary="Get monthly expense settlement calculation and student reimbursements"
)
def get_monthly_settlement(
    monthly_fund_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes the monthly settlement:
    - Starting common fund budget
    - Total COMMON_MONEY spent
    - Current remaining common balance
    - Total PERSONAL_MONEY spent by students
    - Individual student reimbursement amounts owed
    """
    fund = db.query(MonthlyFund).filter(MonthlyFund.id == monthly_fund_id).first()
    if not fund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Monthly fund not found"
        )

    settlement_data = calculate_settlement(db, fund)
    return settlement_data
