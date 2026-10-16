"""
Seed Script: Populates sample data matching the exact required scenario.

Scenario:
- 5 students: Student A, Student B, Student C, Student D, Student E
- Hostel: "NIE Boys Hostel"
- Monthly Fund: October 2026
- Budget Holder: Student A
- Total Common Fund: Rs. 10,000 (5 students x Rs. 2,000)
- Expenses:
  1. Student A -> Rs. 1,500 COMMON_MONEY (Rice - Food)
  2. Student B -> Rs. 800 PERSONAL_MONEY (Vegetables - Food)
  3. Student C -> Rs. 500 PERSONAL_MONEY (Milk - Food)
  4. Student D -> Rs. 300 PERSONAL_MONEY (Cleaning items - Cleaning)

Usage:
  py backend/seed_data.py
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, date

# Ensure backend directory is in sys.path whether run from root or backend/
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.hostel import Hostel, HostelMember
from app.models.monthly_fund import MonthlyFund
from app.models.contribution import Contribution
from app.models.expense import Expense
from app.utils.auth import get_password_hash


def seed():
    print(f"[*] Connecting to database: {settings.resolved_database_url}")
    print("[*] Creating database tables if not existing...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("[*] Checking existing seed data...")
        existing_hostel = db.query(Hostel).filter(Hostel.hostel_name == "NIE Boys Hostel").first()
        if existing_hostel:
            print("[i] 'NIE Boys Hostel' already exists in this database.")
            # Ensure existing students have USN and department
            students_data = [
                ("Student A", "4NI20CS001", "studenta@hostel.com", "Computer Science"),
                ("Student B", "4NI20CS002", "studentb@hostel.com", "Computer Science"),
                ("Student C", "4NI20IS015", "studentc@hostel.com", "Information Science"),
                ("Student D", "4NI20EC030", "studentd@hostel.com", "Electronics & Comm"),
                ("Student E", "4NI20ME042", "studente@hostel.com", "Mechanical Eng"),
            ]
            for name, usn, email, dept in students_data:
                u = db.query(User).filter(User.email == email).first()
                if u:
                    if not u.usn: u.usn = usn
                    if not u.department: u.department = dept
            db.commit()
            print("[i] Seed data verified and ready.")
            return

        print("[*] Creating 5 students...")
        students_data = [
            ("Student A", "4NI20CS001", "studenta@hostel.com", "Computer Science"),
            ("Student B", "4NI20CS002", "studentb@hostel.com", "Computer Science"),
            ("Student C", "4NI20IS015", "studentc@hostel.com", "Information Science"),
            ("Student D", "4NI20EC030", "studentd@hostel.com", "Electronics & Comm"),
            ("Student E", "4NI20ME042", "studente@hostel.com", "Mechanical Eng"),
        ]

        default_password_hash = get_password_hash("password123")
        created_users = []

        for name, usn, email, dept in students_data:
            user = db.query(User).filter(User.email == email).first()
            if not user:
                user = User(
                    name=name,
                    usn=usn,
                    email=email,
                    department=dept,
                    password_hash=default_password_hash
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                if not user.usn:
                    user.usn = usn
                if not user.department:
                    user.department = dept
                db.commit()
            created_users.append(user)

        user_a, user_b, user_c, user_d, user_e = created_users

        print(f"[*] Creating hostel 'NIE Boys Hostel' (Admin: {user_a.name})...")
        hostel = Hostel(
            hostel_name="NIE Boys Hostel",
            created_by=user_a.id
        )
        db.add(hostel)
        db.commit()
        db.refresh(hostel)

        # Add all 5 as members
        print("[*] Enrolling members in NIE Boys Hostel...")
        memberships = [
            (user_a.id, "ADMIN"),
            (user_b.id, "MEMBER"),
            (user_c.id, "MEMBER"),
            (user_d.id, "MEMBER"),
            (user_e.id, "MEMBER"),
        ]
        for uid, role in memberships:
            m = HostelMember(hostel_id=hostel.id, user_id=uid, role=role)
            db.add(m)
        db.commit()

        # Create October 2026 Fund
        print("[*] Creating Monthly Fund: October 2026 (Budget Holder: Student A)...")
        fund = MonthlyFund(
            hostel_id=hostel.id,
            month="October",
            year=2026,
            budget_holder_id=user_a.id,
            total_budget=10000.0,
            current_balance=10000.0,
            status="ACTIVE"
        )
        db.add(fund)
        db.commit()
        db.refresh(fund)

        # Create 5 x 2000 contributions
        print("[*] Recording 5 x Rs. 2,000 monthly contributions (Total Rs. 10,000)...")
        for u in created_users:
            c = Contribution(
                monthly_fund_id=fund.id,
                student_id=u.id,
                amount=2000.0,
                paid=True,
                payment_date=datetime.now(timezone.utc)
            )
            db.add(c)
        db.commit()

        # Add Expenses
        print("[*] Recording sample hostel expenses...")
        # 1. Student A spends Rs. 1,500 COMMON_MONEY (Rice)
        exp1 = Expense(
            monthly_fund_id=fund.id,
            paid_by=user_a.id,
            description="Rice",
            category="Food",
            amount=1500.0,
            payment_source="COMMON_MONEY",
            expense_date=date(2026, 10, 2)
        )
        # Deduct from common balance
        fund.current_balance -= 1500.0
        db.add(exp1)

        # 2. Student B spends Rs. 800 PERSONAL_MONEY (Vegetables)
        exp2 = Expense(
            monthly_fund_id=fund.id,
            paid_by=user_b.id,
            description="Vegetables",
            category="Food",
            amount=800.0,
            payment_source="PERSONAL_MONEY",
            expense_date=date(2026, 10, 4)
        )
        db.add(exp2)

        # 3. Student C spends Rs. 500 PERSONAL_MONEY (Milk)
        exp3 = Expense(
            monthly_fund_id=fund.id,
            paid_by=user_c.id,
            description="Milk",
            category="Food",
            amount=500.0,
            payment_source="PERSONAL_MONEY",
            expense_date=date(2026, 10, 6)
        )
        db.add(exp3)

        # 4. Student D spends Rs. 300 PERSONAL_MONEY (Cleaning items)
        exp4 = Expense(
            monthly_fund_id=fund.id,
            paid_by=user_d.id,
            description="Cleaning items",
            category="Cleaning",
            amount=300.0,
            payment_source="PERSONAL_MONEY",
            expense_date=date(2026, 10, 8)
        )
        db.add(exp4)

        db.commit()

        print("\n" + "=" * 60)
        print("SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Database: {settings.resolved_database_url}")
        print(f"Hostel: {hostel.hostel_name} (ID: {hostel.id})")
        print(f"Monthly Fund: October 2026 (ID: {fund.id})")
        print("Starting Fund: Rs. 10,000.00 | Current Common Balance: Rs. 8,500.00")
        print("Expected Reimbursements:")
        print("  - Student B receives: Rs. 800.00")
        print("  - Student C receives: Rs. 500.00")
        print("  - Student D receives: Rs. 300.00")
        print("  - Total Personal Settlement: Rs. 1,600.00")
        print("\nSample Logins (Password for all: password123):")
        for name, email in students_data:
            print(f"  - {name}: {email}")
        print("=" * 60 + "\n")

    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
