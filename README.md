# Antigravity Pay - Personal Finance Management System (Expense Tracker)

Antigravity Pay is a modern, production-quality Personal Finance Management System featuring a premium glassmorphic UI, rich interactive charts (Chart.js), dark/light mode toggles, multi-currency conversion, automated savings goal progress meters, recurring bill scheduling, CSV imports/exports, OCR receipt logs, and dynamic AI-powered heuristics insights.

---

## Key Features

1. **Dashboard & Analytics:** Visualizes real-time metrics, cumulative outflow trend lines, category donut distributions, and monthly income-vs-expense comparisons.
2. **Dynamic AI Recommendations:** Analyzes saving ratios, identifies overspending categories, computes a **Financial Health Score** (0-100), and forecasts next-month expenditures.
3. **Transaction Management:** Full CRUD logs supporting multi-currency (USD, INR, EUR, GBP, JPY), tagging, location details, and OCR receipt uploads.
4. **Budget Controls:** Set strict monthly or weekly thresholds per category. Automated alerts are dispatched once limits are exceeded.
5. **Milestone Goals:** Fund vacations or emergency accounts with progress trackers.
6. **Bills Calendar:** Schedule upcoming cycles (Rent, Internet, Electricity) with due alerts and automatic transaction logs.
7. **Compiled Reports:** Compile PDF financial statements using ReportLab or download CSV data.
8. **Keyboard Shortcuts:** Fast-track navigation across dashboards.
9. **Docker Support:** Fully containerized with PostgreSQL support.

---

## Tech Stack

- **Backend:** Python 3.13, Django 6.0, Django REST Framework
- **Database:** SQLite (local development fallback) / PostgreSQL (production/docker)
- **Frontend:** Vanilla HTML5/CSS3, JavaScript (ES6+), Bootstrap 5, Chart.js, Bootstrap Icons
- **Document Compiling:** ReportLab (PDF), Pandas / OpenPyXL (Excel/CSV)
- **Deployment:** Docker, Gunicorn, WhiteNoise

---

## Installation & Local Setup

Ensure Python 3.13+ is installed on your local machine.

### 1. Clone & Set Up Directory
```bash
git clone <repository_url>
cd "Expense tracker"
```

### 2. Configure Virtual Environment
```powershell
# Create venv
python -m venv venv

# Activate venv (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Apply Migrations & Seed Mock Data
```powershell
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Load demo records & admin credentials
python manage.py seed_data
```

### 4. Run Development Server
```powershell
python manage.py runserver
```
Visit the dashboard at `http://127.0.0.1:8000/` and sign in.

---

## Docker Compose Setup

Run the entire stack (PostgreSQL + Django + Gunicorn) in containers:

```bash
docker-compose up --build
```
The Django application will run database migrations, load seed data, and start Gunicorn on `http://localhost:8000/`.

---

## Login Credentials

- **Demo Account (Standard User):**
  - **Username:** `demo`
  - **Password:** `Password123`
- **Admin Panel Superuser:**
  - **Username:** `admin`
  - **Password:** `AdminPassword123`
  - **Access Url:** `http://127.0.0.1:8000/admin/`

---

## Keyboard Shortcuts

Navigate swiftly using keyboard combos:

| Shortcut | Description |
| :--- | :--- |
| **`g` + `d`** | Navigate to Dashboard |
| **`g` + `t`** | Navigate to Transactions |
| **`g` + `b`** | Navigate to Budgets |
| **`g` + `g`** | Navigate to Goals |
| **`g` + `i`** | Navigate to Bills |
| **`n`** | Open "New Transaction" Modal |
| **`escape`** | Close Modals |
