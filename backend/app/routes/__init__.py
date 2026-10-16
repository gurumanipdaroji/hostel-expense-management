from app.routes.auth import router as auth_router
from app.routes.hostel import router as hostel_router
from app.routes.members import router as members_router
from app.routes.monthly_fund import router as monthly_fund_router
from app.routes.contributions import router as contributions_router
from app.routes.expenses import router as expenses_router
from app.routes.settlement import router as settlement_router
from app.routes.dashboard import router as dashboard_router

__all__ = [
    "auth_router",
    "hostel_router",
    "members_router",
    "monthly_fund_router",
    "contributions_router",
    "expenses_router",
    "settlement_router",
    "dashboard_router"
]
