import sys
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure backend directory is in sys.path so 'import app...' works from root or anywhere
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, migrate_db_schema
import app.models  # Ensure all models are registered with Base metadata
from app.routes import (
    auth_router,
    hostel_router,
    members_router,
    monthly_fund_router,
    contributions_router,
    expenses_router,
    settlement_router,
    dashboard_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all database tables on application startup
    try:
        Base.metadata.create_all(bind=engine)
        migrate_db_schema()
        print(f"[*] Database initialized: {settings.resolved_database_url}")
    except Exception as e:
        print(f"[Warning] Could not auto-create database tables on startup: {e}")
    yield


tags_metadata = [
    {"name": "Authentication", "description": "Student registration, JWT login, and profile lookup"},
    {"name": "Hostels", "description": "Create and manage hostels and view membership"},
    {"name": "Members", "description": "Add or remove student members in a hostel"},
    {"name": "Monthly Funds", "description": "Manage monthly budgets, budget holders, and periods"},
    {"name": "Contributions", "description": "Track member monthly fund contributions and payments"},
    {"name": "Expenses", "description": "Record COMMON_MONEY and PERSONAL_MONEY hostel expenses"},
    {"name": "Settlement", "description": "Calculate end-of-month student reimbursements and remaining fund"},
    {"name": "Dashboard", "description": "High-level summary cards, recent expenses, and member status"},
]

app = FastAPI(
    title=settings.APP_NAME,
    description="Clean, beginner-friendly REST API for Shared Hostel Expense Management and Monthly Settlement.",
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# CORS middleware configuration: supports local origins and origin regex for flexible local testing ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(auth_router)
app.include_router(hostel_router)
app.include_router(members_router)
app.include_router(monthly_fund_router)
app.include_router(contributions_router)
app.include_router(expenses_router)
app.include_router(settlement_router)
app.include_router(dashboard_router)


@app.get("/", tags=["General"])
def root():
    return {
        "status": "online",
        "message": "Welcome to Hostel Expense Management System API",
        "database_type": "sqlite" if settings.resolved_database_url.startswith("sqlite") else "mysql",
        "docs_url": "/docs",
        "version": "1.0.0"
    }
