# 💰 Personal Expense Tracker (Flask + JSON Database)

A modern, fully-fledged, and responsive **Personal Expense Tracker** web application built with **Python Flask**, clean custom CSS, and **JSON file database storage**.

---

## ✨ Features

- 🔐 **User Authentication**:
  - Secure Signup and Login with `scrypt` password hashing.
  - Session management and `@login_required` route security.
  - Forgot Password simulation flow with token-based reset functionality.
  - User profile update and password change options.
  - Multi-currency support (`$`, `₹`, `€`, `£`, `¥`, `AED`, `C$`, `A$`).

- 📊 **Interactive Dashboard**:
  - Real-time KPI summary cards (Total Spent, Monthly Budget, Remaining Budget, Today's Spend).
  - Visual monthly budget progress bar with automatic 80% and 100% threshold alerts.
  - Interactive Chart.js graphs (Category Breakdown Doughnut & 6-Month Spending Trends Bar Chart).
  - Recent transactions table with instant edit/delete actions.

- 💸 **Comprehensive Expense Management**:
  - **Add / Edit / Delete Expenses**: Track title, amount, category, date, payment method, tags, and notes.
  - **Dynamic Filter & Search**: Filter by keyword, category, payment mode, and date range (`from` & `to`).
  - **Sorting**: Sort by date (newest/oldest) or amount (highest/lowest).
  - **Subtotal Calculations**: Real-time total for any applied filter.

- 🎯 **Monthly Budgeting**:
  - Set custom spending limits for any specific month (`YYYY-MM`).
  - Color-coded progress indicators (Green = Safe, Orange = Warning, Red = Exceeded).

- 📈 **Analytics & Reports**:
  - Dedicated analytics page with spending trends, category distribution, and payment method share.

- 📥 **Data Exporting**:
  - One-click CSV spreadsheet download.
  - Raw JSON data export for backups.

- 💾 **JSON Database Persistence**:
  - `data/users.json`: User accounts, credentials, and password tokens.
  - `data/expenses.json`: User expense items and monthly budget thresholds.
  - No external SQL server required — runs out-of-the-box!

---

## 📁 Project Structure

```text
flask project/
├── app.py                     # Main Flask routing, controllers, and session logic
├── models.py                  # JSON Database Engine (Data access layer for users & expenses)
├── seed_demo_data.py          # Script to generate demo user & realistic sample expenses
├── test_app.py                # Automated unit and integration test suite
├── requirements.txt           # Python project dependencies
├── data/
│   ├── users.json             # JSON storage for user profiles and hashed passwords
│   └── expenses.json          # JSON storage for expense items and budget limits
├── static/
│   ├── css/
│   │   └── style.css          # Custom, modern responsive styling (Mobile + Desktop)
│   └── js/
│       └── main.js            # Client-side mobile navbar, flash dismissals & modal helpers
├── templates/
│   ├── base.html              # Base template with navigation, alerts, footer & Chart.js
│   ├── index.html             # Landing homepage
│   ├── dashboard.html         # Main overview dashboard with charts and KPIs
│   ├── budget.html            # Monthly budget setting & status
│   ├── analytics.html         # Detailed graphs and breakdown tables
│   ├── profile.html           # Profile settings & change password
│   ├── auth/
│   │   ├── login.html         # Login page
│   │   ├── signup.html        # Registration page
│   │   ├── forgot_password.html # Password reset request
│   │   └── reset_password.html  # Set new password page
│   ├── expenses/
│   │   ├── list.html          # Filterable & searchable expense table
│   │   ├── add.html           # Add new expense form
│   │   └── edit.html          # Edit expense form
│   └── errors/
│       ├── 404.html           # Page not found error
│       └── 500.html           # Internal server error
└── README.md                  # Quickstart documentation
```

---

## 🚀 Quickstart & How to Run

### 1. Requirements
- Python 3.8+ installed on your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Seed Demo Data
To immediately test the application with realistic data:
```bash
python seed_demo_data.py
```
*Demo Login Credentials:*
- **Username / Email**: `demo` (or `demo@example.com`)
- **Password**: `password123`

### 4. Start the Flask Application
```bash
python app.py
```

### 5. Access the Web Application
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Running Automated Tests

Run the complete test suite anytime to verify backend integrity:
```bash
python -m unittest test_app.py
```
