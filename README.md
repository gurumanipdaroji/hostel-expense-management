# Hostel Expense Management System

> A clean, beginner-friendly full-stack web application for shared hostel expenses, common fund tracking, and monthly reimbursement settlement. Built for college students learning full-stack development, ready for GitHub and future deployment on AWS EC2.

---

## 1. Project Overview

Living in a hostel or shared student apartment involves shared expenses: rice, vegetables, drinking water cans, gas cylinder refills, electricity bills, and cleaning items.

Unlike a generic hostel CRUD system, this project solves the real-world problem of **Shared Living Financial Management**:
- At the beginning of each month, roommates contribute an agreed-upon equal amount (e.g. ₹2,000 each) into a single monthly common fund.
- One selected student acts as the **Budget Holder** who holds this common cash fund.
- During the month, purchases happen in two distinct ways:
  1. **Common Money:** The budget holder pays for items using the common fund (reduces the common balance).
  2. **Personal Money:** Any roommate buys an item using their own pocket money (does *not* reduce common balance, but records reimbursement owed to that student).
- At the end of the month, the system computes the exact **Settlement**: how much remaining common money exists, and the exact amounts the budget holder must reimburse to students who paid personally.

---

## 2. Main Features

- **JWT Authentication:** Secure user registration, password hashing with bcrypt, and token-based login.
- **Hostel Creation & Membership:** Users can create a hostel (e.g., *NIE Boys Hostel*), invite roommates by email, and manage roles (ADMIN, MEMBER).
- **Dynamic Monthly Funds:** Any number of roommates (4, 5, 6, etc.) can be configured dynamically with customizable per-student contributions.
- **Dual Expense Engine:**
  - `COMMON_MONEY`: Automatically validates that expense &le; current common balance, preventing overdrafts.
  - `PERSONAL_MONEY`: Keeps common balance intact while queuing reimbursement.
- **Automated Settlement Service:** Calculates starting fund, total common spent, current common balance, total personal spent, and per-student reimbursement figures.
- **Comprehensive Dashboard:** 6 interactive KPI cards, recent expense feed, member contribution checklist, and quick action modals.
- **Expense History & Filters:** Filter expenses by category (Food, Groceries, Electricity, etc.), student payer, and payment source.
- **Monthly History:** Review and compare previous months' budgets and balances.
- **Interactive Swagger Documentation:** Built-in interactive API docs at `/docs`.

---

## 3. Technology Stack

### Backend
- **Python 3.10+**
- **FastAPI**: High-performance, modern REST API framework
- **SQLAlchemy**: Clean Python ORM with relational foreign keys
- **MySQL / PyMySQL**: Relational database storage
- **Pydantic V2**: Robust request validation & serializable response schemas
- **PyJWT & Bcrypt**: Secure token-based authentication and password hashing
- **Uvicorn**: Lightweight ASGI web server
- **Pytest**: Automated test suite for all business logic rules

### Frontend
- **HTML5 & Vanilla JavaScript**: Clean, beginner-friendly architecture without complicated build steps or Node.js runtime dependencies.
- **CSS3 & Bootstrap 5 (CDN)**: Modern, responsive UI with Bootstrap Icons.
- **Centralized Config (`config.js`)**: Single `BASE_URL` variable, making AWS EC2 deployment as simple as updating one line.

---

## 4. Folder Structure

```
hostelexpensemanagament/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app instance, CORS & lifespan
│   │   ├── database.py          # SQLAlchemy engine, session & get_db dependency
│   │   ├── config.py            # Pydantic BaseSettings & env configs
│   │   │
│   │   ├── models/              # SQLAlchemy database tables
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User accounts
│   │   │   ├── hostel.py        # Hostel & HostelMember relations
│   │   │   ├── monthly_fund.py  # Monthly budgets & budget holder
│   │   │   ├── contribution.py  # Member monthly contributions
│   │   │   └── expense.py       # COMMON_MONEY & PERSONAL_MONEY records
│   │   │
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── hostel.py
│   │   │   ├── monthly_fund.py
│   │   │   ├── contribution.py
│   │   │   └── expense.py
│   │   │
│   │   ├── routes/              # Clean API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # /auth/register, /auth/login, /auth/me
│   │   │   ├── hostel.py        # /hostels
│   │   │   ├── members.py       # /hostels/{id}/members
│   │   │   ├── monthly_fund.py  # /monthly-funds
│   │   │   ├── contributions.py # /contributions
│   │   │   ├── expenses.py      # /expenses
│   │   │   ├── settlement.py    # /settlement/{fund_id}
│   │   │   └── dashboard.py     # /dashboard/{fund_id}
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── auth.py          # Password hashing, JWT token creation/verification
│   │       └── settlement.py    # Core business settlement math engine
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   └── test_business_logic.py # 9 unit tests verifying business rules
│   │
│   ├── requirements.txt         # Backend Python dependencies
│   ├── .env.example             # Template for environment configuration
│   ├── seed_data.py             # Script to populate the exact 5-student scenario
│   └── README.md                # Backend quick-start guide
│
├── frontend/
│   ├── index.html               # Public landing page explaining the system
│   ├── login.html               # Sign-in page with quick-fill demo buttons
│   ├── register.html            # Student registration page
│   ├── dashboard.html           # Main metric cards, recent expenses & member status
│   ├── members.html             # Member directory & monthly contribution tracking
│   ├── expenses.html            # Add and filter common/personal expenses
│   ├── settlement.html          # End-of-month reimbursement calculation breakdown
│   ├── monthly-history.html     # Past months overview & records
│   │
│   ├── css/
│   │   └── style.css            # Custom responsive styles & badges
│   │
│   └── js/
│       ├── config.js            # Single BASE_URL configuration for local and AWS
│       ├── auth.js              # Token management, navbar rendering & authFetch
│       ├── login.js             # Sign-in logic
│       ├── register.js          # Registration & auto-login logic
│       ├── dashboard.js         # Dashboard data loading & modal controllers
│       ├── members.js           # Member management & contribution actions
│       ├── expenses.js          # Expense creation, filters & deletion
│       ├── settlement.js        # Settlement calculation view & month closing
│       └── monthly-history.js   # Past monthly fund cards loader
│
├── .gitignore                   # Ignores .env, venv, cache, IDE files, etc.
├── LICENSE                      # MIT Open Source License
└── README.md                    # Project documentation
```

---

## 5. Database Setup (MySQL)

Ensure MySQL server is installed and running on your system.

### Create Database
Open your MySQL Command Line Client or MySQL Workbench:
```sql
CREATE DATABASE hostel_management;
```

You do not need to manually write `CREATE TABLE` statements. FastAPI and SQLAlchemy will **automatically generate all tables** (`users`, `hostels`, `hostel_members`, `monthly_funds`, `contributions`, `expenses`) the first time the backend starts!

---

## 6. Backend Setup

### Step 1: Open a terminal in the project directory
```bash
cd backend
```

### Step 2: Create a Python virtual environment
```bash
# On Windows
py -m venv venv
.\venv\Scripts\activate

# On Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure environment variables
Copy `.env.example` to `.env`:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Open `.env` and adjust your MySQL password:
```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/hostel_management
SECRET_KEY=my_secure_dev_key_2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
CORS_ORIGINS=http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000,*
```

*(Note: If testing without a running MySQL instance, you can temporarily set `DATABASE_URL=sqlite:///./hostel_management.db` in `.env`).*

---

## 7. Sample Data (Optional Quick Seeding)

To instantly populate the database with the exact 5-student scenario:
```bash
py seed_data.py
```
This automatically sets up:
- **5 Students:** Student A (`studenta@hostel.com`), Student B, Student C, Student D, Student E (Password for all: `password123`).
- **Hostel:** "NIE Boys Hostel"
- **Monthly Fund:** October 2026 (Budget: ₹10,000, Budget Holder: Student A)
- **Contributions:** 5 &times; ₹2,000 (PAID)
- **Expenses:**
  - A spends ₹1,500 COMMON_MONEY (Rice)
  - B spends ₹800 PERSONAL_MONEY (Vegetables)
  - C spends ₹500 PERSONAL_MONEY (Milk)
  - D spends ₹300 PERSONAL_MONEY (Cleaning items)

---

## 8. How to Run Locally

### 1. Start the FastAPI Backend
From the project root:
```bash
py -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend will be live at: `http://127.0.0.1:8000`

### 2. Run the Frontend
Because the frontend is static HTML, CSS, and JavaScript, you can run it using any simple local server:

**Option A (VS Code Live Server):**
- Right-click `frontend/index.html` in VS Code and click **"Open with Live Server"** (usually runs on `http://127.0.0.1:5500`).

**Option B (Python Simple HTTP Server):**
Open a new terminal window in the `frontend/` directory:
```bash
cd frontend
py -m http.server 5500
```
Open your browser and navigate to:
[http://127.0.0.1:5500](http://127.0.0.1:5500)

---

## 9. API Documentation

FastAPI provides automatic interactive Swagger documentation:
- **Interactive Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Redoc Alternative:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

All endpoints are organized into clean Swagger tags:
1. **Authentication:** `/auth/register`, `/auth/login`, `/auth/me`
2. **Hostels:** `/hostels`, `/hostels/{id}`
3. **Members:** `/hostels/{id}/members`
4. **Monthly Funds:** `/monthly-funds`, `/hostels/{id}/monthly-funds`
5. **Contributions:** `/contributions`, `/monthly-funds/{id}/contributions`
6. **Expenses:** `/expenses`, `/monthly-funds/{id}/expenses`
7. **Settlement:** `/settlement/{fund_id}`
8. **Dashboard:** `/dashboard/{fund_id}`

---

## 10. Example Hostel Scenario & Business Logic

### Scenario Details
- **5 Students:** Student A, Student B, Student C, Student D, Student E
- **Monthly Contribution:** ₹2,000 each
- **Starting Common Fund:** ₹10,000 (5 &times; ₹2,000)
- **Budget Holder:** Student A (holds the ₹10,000 common money)

### Expenses Incurred
| Date | Description | Paid By | Payment Source | Amount | Impact on Common Balance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Oct 2 | Rice | Student A | `COMMON_MONEY` | ₹1,500 | Deducted (₹10,000 &minus; ₹1,500 = ₹8,500) |
| Oct 4 | Vegetables | Student B | `PERSONAL_MONEY`| ₹800 | None (Balance stays ₹8,500; B is owed ₹800) |
| Oct 6 | Milk | Student C | `PERSONAL_MONEY`| ₹500 | None (Balance stays ₹8,500; C is owed ₹500) |
| Oct 8 | Cleaning | Student D | `PERSONAL_MONEY`| ₹300 | None (Balance stays ₹8,500; D is owed ₹300) |

### End-of-Month Settlement
```
Starting Common Fund:           ₹10,000
Total COMMON_MONEY Expenses:   - ₹1,500
----------------------------------------
Current Common Balance:          ₹8,500   (Held by Student A)

Total PERSONAL_MONEY Expenses:   ₹1,600   (To be reimbursed to students)

Student Reimbursements:
  - Student B receives:           ₹800
  - Student C receives:           ₹500
  - Student D receives:           ₹300
----------------------------------------
Total Settlement Amount:         ₹1,600

Net Leftover Common Fund:        ₹6,900   (₹8,500 - ₹1,600)
```

### Core Business Rules Implemented
- **Rule 1:** Dynamic members and total budget (4 &times; ₹2,000 = ₹8,000; 6 &times; ₹2,000 = ₹12,000).
- **Rule 2:** Exactly one student acts as Budget Holder per month.
- **Rule 3:** `COMMON_MONEY` directly reduces `current_balance`.
- **Rule 4:** `PERSONAL_MONEY` does **not** reduce `current_balance`.
- **Rule 5:** `PERSONAL_MONEY` generates reimbursement credit owed to that student.
- **Rule 6:** Every expense stores: payer, description, category, amount, payment source, date, and monthly fund ID.
- **Rule 7:** Invalid common expenses are rejected (e.g. spending ₹9,000 when balance is ₹8,500 returns 400 *Insufficient common balance*).
- **Rule 8 & 9:** Distinct separation between *money remaining in common fund* and *money owed to students*.

---

## 11. Automated Testing

Run the test suite to verify all business rules:
```bash
py -m pytest backend/tests/test_business_logic.py -v
```

Tests included:
1. `test_user_registration`: Validates user creation and password hashing.
2. `test_user_login`: Validates JWT token generation and authentication.
3. `test_hostel_creation`: Verifies hostel creation and automatic admin membership.
4. `test_monthly_fund_creation`: Validates budget holder assignment and initial balance.
5. `test_contributions`: Checks recording and updating member contributions.
6. `test_common_money_expense_reduces_balance`: Verifies common money deduction.
7. `test_personal_money_expense_does_not_reduce_balance`: Verifies personal money does not deduct common balance.
8. `test_insufficient_common_balance_rejected`: Verifies overdraft protection.
9. `test_settlement_calculation_and_example_scenario`: Verifies the exact 5-student numbers (Common Balance = ₹8,500; B receives ₹800, C receives ₹500, D receives ₹300, Total personal settlement = ₹1,600).

---

## 12. How to Push to GitHub

When you are ready to push this complete project to your GitHub account:

### Step 1: Initialize Git
```bash
git init
```

### Step 2: Verify `.gitignore`
Make sure `.env`, `venv/`, and `__pycache__/` are ignored (already pre-configured in `.gitignore`):
```bash
git status
```

### Step 3: Stage and Commit Files
```bash
git add .
git commit -m "Initial commit: Hostel Expense Management System full-stack application"
```

### Step 4: Link your GitHub repository and Push
Create a new public repository on GitHub (e.g., `hostel-expense-management`), then run:
```bash
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/hostel-expense-management.git
git push -u origin main
```

---

## 13. Future AWS Deployment

When you are ready to deploy this application on AWS EC2, you can use standard college deployment scripts (similar to `ser2.sh`, `ser3.sh`, `cli2.sh`, `cli3.sh`):

### Architecture Overview
```
+------------------------------------+        +------------------------------------+
|            Frontend EC2            |        |            Backend EC2             |
|   (Public IP: FRONTEND_IP)         |        |   (Public IP: BACKEND_IP)          |
|                                    |        |                                    |
|   - Apache Web Server (Port 80)    | -----> |   - FastAPI / Uvicorn (Port 8000)  |
|   - Serves HTML, CSS, JavaScript   |        |   - MySQL Database (Port 3306)     |
|   - config.js -> BACKEND_IP:8000   |        |   - CORS allows FRONTEND_IP        |
+------------------------------------+        +------------------------------------+
```

### Backend EC2 Setup
1. Launch an Ubuntu EC2 instance (`t2.micro` or `t3.micro`).
2. Open Security Group inbound rules:
   - Port 22 (SSH)
   - Port 8000 (FastAPI Backend)
   - Port 3306 (MySQL, internal or restricted to EC2)
3. Connect via SSH and run:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv mysql-server git
   
   # Clone repository
   git clone https://github.com/<YOUR_GITHUB_USERNAME>/hostel-expense-management.git
   cd hostel-expense-management/backend
   
   # Create virtual environment and install packages
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Setup MySQL and .env
   cp .env.example .env
   # Edit .env with your MySQL credentials and CORS
   
   # Run FastAPI server
   nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
   ```

### Frontend EC2 Setup
1. Launch an Ubuntu EC2 instance for the Frontend.
2. Open Security Group inbound rules:
   - Port 22 (SSH)
   - Port 80 (HTTP Apache)
3. Connect via SSH and run:
   ```bash
   sudo apt update
   sudo apt install -y apache2 git
   
   # Clone repository
   git clone https://github.com/<YOUR_GITHUB_USERNAME>/hostel-expense-management.git
   
   # Update backend URL in frontend/js/config.js:
   # const BASE_URL = "http://<YOUR_BACKEND_EC2_PUBLIC_IP>:8000";
   
   # Copy static frontend files to Apache www root
   sudo cp -r hostel-expense-management/frontend/* /var/www/html/
   sudo systemctl restart apache2
   ```
4. Access your web app in your browser at `http://<YOUR_FRONTEND_EC2_PUBLIC_IP>`.

---

## 14. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
