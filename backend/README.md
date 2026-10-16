# Hostel Expense Management System - Backend

This is the FastAPI backend for the **Hostel Expense Management System**. It manages authentication, hostel rooms/members, monthly common budgets, expense tracking, and settlement calculations.

## Technology Stack
- **Python 3.10+**
- **FastAPI** (REST API framework)
- **SQLAlchemy** (ORM)
- **PyMySQL / MySQL** (Database connector)
- **Pydantic V2** (Data validation & schemas)
- **PyJWT & Bcrypt** (Secure JWT authentication and password hashing)
- **Pytest** (Automated business logic test suite)

## Quick Start (Local Setup)

### 1. Create and Activate Virtual Environment
```bash
# Windows
py -m venv venv
.\venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env     # Windows
cp .env.example .env       # Linux / macOS
```
Edit `.env` to configure your MySQL database credentials:
```env
DATABASE_URL=mysql+pymysql://root:yourpassword@localhost:3306/hostel_management
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000,*
```

### 4. Create MySQL Database
```sql
CREATE DATABASE hostel_management;
```

### 5. Seed Sample Data (Optional)
Populate 5 students, 1 hostel, October 2026 fund, and sample expenses:
```bash
py seed_data.py
```

### 6. Run the FastAPI Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive Swagger API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Alternative Redoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 7. Run Unit & Business Logic Tests
```bash
pytest backend/tests/test_business_logic.py -v
```
All 9 core business logic tests will execute and verify the shared expense rules and settlement math.
