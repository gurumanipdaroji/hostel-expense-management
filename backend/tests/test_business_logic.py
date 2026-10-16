import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# Create an in-memory SQLite database for test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create a fresh database schema before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_and_login_user(name: str, email: str, password: str = "pass123"):
    """Helper to register and login a user, returning user data and JWT headers."""
    reg_res = client.post("/auth/register", json={
        "name": name,
        "email": email,
        "password": password
    })
    assert reg_res.status_code == 201

    login_res = client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    user = login_res.json()["user"]
    headers = {"Authorization": f"Bearer {token}"}
    return user, headers


def test_user_registration():
    """1. Test user registration."""
    res = client.post("/auth/register", json={
        "name": "Student A",
        "email": "studenta@example.com",
        "password": "securepassword123"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Student A"
    assert data["email"] == "studenta@example.com"
    assert "id" in data


def test_user_login():
    """2. Test user login and token generation."""
    client.post("/auth/register", json={
        "name": "Student B",
        "email": "studentb@example.com",
        "password": "mypassword"
    })
    login_res = client.post("/auth/login", json={
        "email": "studentb@example.com",
        "password": "mypassword"
    })
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "studentb@example.com"


def test_hostel_creation():
    """3. Test hostel creation and auto-membership."""
    user, headers = create_and_login_user("Admin Student", "admin@hostel.com")
    hostel_res = client.post("/hostels", json={"hostel_name": "NIE Boys Hostel"}, headers=headers)
    assert hostel_res.status_code == 201
    data = hostel_res.json()
    assert data["hostel_name"] == "NIE Boys Hostel"
    assert data["member_count"] == 1


def test_monthly_fund_creation():
    """4. Test monthly fund creation with budget holder."""
    user, headers = create_and_login_user("Budget Guy", "holder@hostel.com")
    hostel = client.post("/hostels", json={"hostel_name": "Campus Wing A"}, headers=headers).json()

    fund_res = client.post("/monthly-funds", json={
        "hostel_id": hostel["id"],
        "month": "October",
        "year": 2026,
        "budget_holder_id": user["id"],
        "total_budget": 5000.0
    }, headers=headers)

    assert fund_res.status_code == 201
    data = fund_res.json()
    assert data["month"] == "October"
    assert data["year"] == 2026
    assert data["total_budget"] == 5000.0
    assert data["current_balance"] == 5000.0


def test_contributions():
    """5. Test adding and updating contributions."""
    user, headers = create_and_login_user("Student A", "studenta_contrib@example.com")
    hostel = client.post("/hostels", json={"hostel_name": "Wing B"}, headers=headers).json()

    fund = client.post("/monthly-funds", json={
        "hostel_id": hostel["id"],
        "month": "October",
        "year": 2026,
        "budget_holder_id": user["id"],
        "total_budget": 0.0
    }, headers=headers).json()

    contrib_res = client.post("/contributions", json={
        "monthly_fund_id": fund["id"],
        "student_id": user["id"],
        "amount": 2000.0,
        "paid": True
    }, headers=headers)

    assert contrib_res.status_code == 201
    assert contrib_res.json()["amount"] == 2000.0
    assert contrib_res.json()["paid"] is True


def test_common_money_expense_reduces_balance():
    """6. Test COMMON_MONEY expense deducts current common balance."""
    user, headers = create_and_login_user("Student A", "spend_a@example.com")
    hostel = client.post("/hostels", json={"hostel_name": "Wing C"}, headers=headers).json()

    fund = client.post("/monthly-funds", json={
        "hostel_id": hostel["id"],
        "month": "October",
        "year": 2026,
        "budget_holder_id": user["id"],
        "total_budget": 5000.0
    }, headers=headers).json()

    exp_res = client.post("/expenses", json={
        "monthly_fund_id": fund["id"],
        "paid_by": user["id"],
        "description": "Common Rice Bag",
        "category": "Food",
        "amount": 1500.0,
        "payment_source": "COMMON_MONEY"
    }, headers=headers)

    assert exp_res.status_code == 201
    
    # Check fund balance updated
    fund_check = client.get(f"/monthly-funds/{fund['id']}", headers=headers).json()
    assert fund_check["current_balance"] == 3500.0


def test_personal_money_expense_does_not_reduce_balance():
    """7. Test PERSONAL_MONEY expense does NOT deduct common balance."""
    user, headers = create_and_login_user("Student B", "spend_b@example.com")
    hostel = client.post("/hostels", json={"hostel_name": "Wing D"}, headers=headers).json()

    fund = client.post("/monthly-funds", json={
        "hostel_id": hostel["id"],
        "month": "October",
        "year": 2026,
        "budget_holder_id": user["id"],
        "total_budget": 5000.0
    }, headers=headers).json()

    exp_res = client.post("/expenses", json={
        "monthly_fund_id": fund["id"],
        "paid_by": user["id"],
        "description": "Vegetables from pocket",
        "category": "Food",
        "amount": 800.0,
        "payment_source": "PERSONAL_MONEY"
    }, headers=headers)

    assert exp_res.status_code == 201

    # Common balance should remain unchanged at 5000.0
    fund_check = client.get(f"/monthly-funds/{fund['id']}", headers=headers).json()
    assert fund_check["current_balance"] == 5000.0


def test_insufficient_common_balance_rejected():
    """8. Test that COMMON_MONEY expense exceeding balance is rejected."""
    user, headers = create_and_login_user("Student A", "broke_a@example.com")
    hostel = client.post("/hostels", json={"hostel_name": "Wing E"}, headers=headers).json()

    fund = client.post("/monthly-funds", json={
        "hostel_id": hostel["id"],
        "month": "October",
        "year": 2026,
        "budget_holder_id": user["id"],
        "total_budget": 1000.0
    }, headers=headers).json()

    exp_res = client.post("/expenses", json={
        "monthly_fund_id": fund["id"],
        "paid_by": user["id"],
        "description": "Too expensive item",
        "category": "Food",
        "amount": 1500.0,
        "payment_source": "COMMON_MONEY"
    }, headers=headers)

    assert exp_res.status_code == 400
    assert "Insufficient common balance" in exp_res.json()["detail"]


def test_settlement_calculation_and_example_scenario():
    """
    9. Crucial Test: The exact required scenario.
    
    Scenario:
    5 students: Student A, Student B, Student C, Student D, Student E.
    ₹2,000 each -> Total common budget = ₹10,000.
    Student A is Budget Holder.
    
    Expenses:
    - A spends ₹1,500 COMMON_MONEY (Rice)
    - B spends ₹800 PERSONAL_MONEY (Vegetables)
    - C spends ₹500 PERSONAL_MONEY (Milk)
    - D spends ₹300 PERSONAL_MONEY (Cleaning items)
    
    Expected Outcomes:
    - Common balance = ₹8,500
    - B receives = ₹800
    - C receives = ₹500
    - D receives = ₹300
    - Total personal settlement = ₹1,600
    """
    # 1. Create the 5 students
    user_a, headers_a = create_and_login_user("Student A", "studenta@hostel.com")
    user_b, _ = create_and_login_user("Student B", "studentb@hostel.com")
    user_c, _ = create_and_login_user("Student C", "studentc@hostel.com")
    user_d, _ = create_and_login_user("Student D", "studentd@hostel.com")
    user_e, _ = create_and_login_user("Student E", "studente@hostel.com")

    # 2. Student A creates the hostel
    hostel_res = client.post("/hostels", json={"hostel_name": "NIE Boys Hostel"}, headers=headers_a)
    hostel_id = hostel_res.json()["id"]

    # 3. Add B, C, D, E to the hostel
    for email in ["studentb@hostel.com", "studentc@hostel.com", "studentd@hostel.com", "studente@hostel.com"]:
        client.post(f"/hostels/{hostel_id}/members", json={"email": email, "role": "MEMBER"}, headers=headers_a)

    # 4. Create October 2026 Monthly Fund with Student A as Budget Holder and ₹2,000 per student (Total ₹10,000)
    fund_res = client.post("/monthly-funds", json={
        "hostel_id": hostel_id,
        "month": "October",
        "year": 2026,
        "budget_holder_id": user_a["id"],
        "per_student_contribution": 2000.0,
        "total_budget": 10000.0
    }, headers=headers_a)
    assert fund_res.status_code == 201
    fund_id = fund_res.json()["id"]

    # Verify initial common balance is 10,000
    assert fund_res.json()["total_budget"] == 10000.0
    assert fund_res.json()["current_balance"] == 10000.0

    # 5. Record the expenses:
    # A spends ₹1,500 COMMON_MONEY (Rice)
    res1 = client.post("/expenses", json={
        "monthly_fund_id": fund_id,
        "paid_by": user_a["id"],
        "description": "Rice",
        "category": "Food",
        "amount": 1500.0,
        "payment_source": "COMMON_MONEY"
    }, headers=headers_a)
    assert res1.status_code == 201

    # B spends ₹800 PERSONAL_MONEY (Vegetables)
    res2 = client.post("/expenses", json={
        "monthly_fund_id": fund_id,
        "paid_by": user_b["id"],
        "description": "Vegetables",
        "category": "Food",
        "amount": 800.0,
        "payment_source": "PERSONAL_MONEY"
    }, headers=headers_a)
    assert res2.status_code == 201

    # C spends ₹500 PERSONAL_MONEY (Milk)
    res3 = client.post("/expenses", json={
        "monthly_fund_id": fund_id,
        "paid_by": user_c["id"],
        "description": "Milk",
        "category": "Food",
        "amount": 500.0,
        "payment_source": "PERSONAL_MONEY"
    }, headers=headers_a)
    assert res3.status_code == 201

    # D spends ₹300 PERSONAL_MONEY (Cleaning items)
    res4 = client.post("/expenses", json={
        "monthly_fund_id": fund_id,
        "paid_by": user_d["id"],
        "description": "Cleaning items",
        "category": "Cleaning",
        "amount": 300.0,
        "payment_source": "PERSONAL_MONEY"
    }, headers=headers_a)
    assert res4.status_code == 201

    # 6. Call Settlement API
    settlement_res = client.get(f"/settlement/{fund_id}", headers=headers_a)
    assert settlement_res.status_code == 200
    s_data = settlement_res.json()

    # 7. Check All Business Assertions
    # Common balance must be Starting (10,000) - Common money (1,500) = 8,500
    assert s_data["starting_budget"] == 10000.0
    assert s_data["total_common_expenses"] == 1500.0
    assert s_data["current_common_balance"] == 8500.0

    # Total personal expenses must be 800 + 500 + 300 = 1,600
    assert s_data["total_personal_expenses"] == 1600.0
    assert s_data["total_settlement_amount"] == 1600.0

    # Remaining after settlement = 8500 - 1600 = 6900
    assert s_data["remaining_after_settlement"] == 6900.0

    # Verify per-student settlement
    student_map = {s["student_id"]: s for s in s_data["students"]}

    assert student_map[user_b["id"]]["personal_expenses"] == 800.0
    assert student_map[user_b["id"]]["amount_to_receive"] == 800.0

    assert student_map[user_c["id"]]["personal_expenses"] == 500.0
    assert student_map[user_c["id"]]["amount_to_receive"] == 500.0

    assert student_map[user_d["id"]]["personal_expenses"] == 300.0
    assert student_map[user_d["id"]]["amount_to_receive"] == 300.0

    assert student_map[user_a["id"]]["amount_to_receive"] == 0.0
    assert student_map[user_e["id"]]["amount_to_receive"] == 0.0
