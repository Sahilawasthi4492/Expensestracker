# 📖 Personal Expense Tracker - Detailed Step-by-Step Documentation

This document explains the architecture, design choices, JSON database structures, routing logic, and step-by-step implementation of the **Personal Expense Tracker** Flask application.

---

## 📑 Table of Contents
1. [Project Overview & Architecture](#1-project-overview--architecture)
2. [JSON Database Design & Storage Schema](#2-json-database-design--storage-schema)
3. [Authentication & Security Flow](#3-authentication--security-flow)
4. [Routing & Controller Architecture](#4-routing--controller-architecture)
5. [Frontend & Responsive CSS Architecture](#5-frontend--responsive-css-architecture)
6. [Interactive Analytics & Charts](#6-interactive-analytics--charts)
7. [Testing & Verification](#7-testing--verification)
8. [Step-by-Step Implementation Log](#8-step-by-step-implementation-log)

---

## 1. Project Overview & Architecture

The application follows the **Model-View-Template (MVT)** architectural pattern adapted for Flask:

```text
       ┌────────────────────────────────────────────────────────┐
       │                 Web Browser (Client)                   │
       └───────────────────────────┬────────────────────────────┘
                                   │ HTTP Requests (GET, POST)
                                   ▼
┌───────────────────────────────────────────────────────────────────────┐
│                          Flask Application                            │
│                                                                       │
│  app.py: Routing, Session Auth, Form Handling, Filters, Exports        │
│  models.py: JSON File I/O, Atomic Writes, User/Expense/Budget Logic   │
└──────────────────┬─────────────────────────────────┬──────────────────┘
                   │                                 │
                   ▼                                 ▼
   ┌──────────────────────────────┐   ┌──────────────────────────────┐
   │        Jinja2 Views          │   │      JSON File Storage       │
   │ templates/*.html             │   │ data/users.json              │
   │ static/css/style.css         │   │ data/expenses.json           │
   │ static/js/main.js            │   └──────────────────────────────┘
   └──────────────────────────────┘
```

---

## 2. JSON Database Design & Storage Schema

Rather than requiring an external database server (like MySQL or PostgreSQL), the application persists all data in two structured JSON documents inside the `data/` folder.

### A. `data/users.json`
Stores an array of user profile objects:
```json
[
  {
    "id": "1",
    "full_name": "Alex Morgan",
    "username": "demo",
    "email": "demo@example.com",
    "password_hash": "scrypt:32768:8:1$...",
    "currency": "$",
    "created_at": "2026-09-03 15:00:00",
    "reset_token": "random_secure_urlsafe_token",
    "reset_token_expires": "2026-09-03 16:00:00"
  }
]
```

### B. `data/expenses.json`
Stores user-associated expenses and monthly budget settings:
```json
{
  "expenses": [
    {
      "id": "1",
      "user_id": "1",
      "title": "Whole Foods Grocery",
      "amount": 142.80,
      "category": "Food & Dining",
      "date": "2026-09-01",
      "payment_method": "Credit Card",
      "notes": "Fresh vegetables and milk",
      "tags": ["groceries", "food"],
      "created_at": "2026-09-03 15:00:00"
    }
  ],
  "budgets": {
    "1": {
      "2026-09": 2500.0,
      "default": 2500.0
    }
  }
}
```

### C. Safe & Atomic File Writing
To prevent file corruption during simultaneous read/write actions, `models.py` writes changes to a temporary file (`.tmp`) first and uses `os.replace` to replace the target JSON atomically.

---

## 3. Authentication & Security Flow

1. **Password Hashing**: Passwords are never stored in plaintext. They are hashed using `werkzeug.security.generate_password_hash(password, method='scrypt')`.
2. **Session Security**: Session cookies are signed with Flask's secret key.
3. **Route Guarding**: The `@login_required` decorator ensures unauthenticated visitors are redirected to `/login` with a helpful notification.
4. **Forgot Password Flow**:
   - User inputs their email on `/forgot-password`.
   - A 32-character cryptographically secure token (`secrets.token_urlsafe(32)`) with a 1-hour expiration timestamp is generated.
   - The user visits `/reset-password/<token>` to set a new password.

---

## 4. Routing & Controller Architecture

| Route | Method | Protected | Description |
|---|---|---|---|
| `/` | `GET` | No | Landing page with feature highlights and call-to-actions. |
| `/signup` | `GET`, `POST` | No | User registration with validation. |
| `/login` | `GET`, `POST` | No | Sign in via Email or Username with "Remember Me". |
| `/logout` | `GET` | Yes | Clear session and return to login. |
| `/forgot-password` | `GET`, `POST` | No | Generate password reset token. |
| `/reset-password/<token>` | `GET`, `POST` | No | Set new password using token. |
| `/profile` | `GET`, `POST` | Yes | Update profile details and change password. |
| `/dashboard` | `GET` | Yes | High-level metrics, budget progress bar, recent items, and charts. |
| `/expenses` | `GET` | Yes | Tabulated expenses with keyword search, category & date filters, and sorting. |
| `/expenses/add` | `GET`, `POST` | Yes | Form to create a new expense item. |
| `/expenses/edit/<id>` | `GET`, `POST` | Yes | Edit an existing expense item. |
| `/expenses/delete/<id>` | `POST` | Yes | Remove an expense with browser confirmation. |
| `/budget` | `GET`, `POST` | Yes | Set monthly spending limits and check utilization. |
| `/analytics` | `GET` | Yes | Detailed visual charts (Trends, Categories, Payment methods). |
| `/export/csv` | `GET` | Yes | Download current filtered expense table as a CSV file. |
| `/export/json` | `GET` | Yes | Download all user records in JSON format. |

---

## 5. Frontend & Responsive CSS Architecture

- **CSS Variables**: Unified color palette (`--primary: #4f46e5`, `--success: #10b981`, etc.) defined in `:root` for easy styling tweaks.
- **Mobile Navigation**: Hamburger menu toggle that collapses neatly on smaller screens.
- **Card-Based UI**: Clean, rounded card containers with subtle drop shadows and hover animations.
- **Color-Coded Badges**: Distinct pastel badges for categories (Food, Shopping, Transportation, Bills, Entertainment, Health).
- **Interactive Flash Alerts**: Toast notifications that auto-dismiss after 5 seconds or on close-button click.

---

## 6. Interactive Analytics & Charts

Charts are rendered on HTML5 Canvas using **Chart.js**:
1. **Category Breakdown**: Doughnut chart showing proportions of spending across categories.
2. **Monthly Trends**: Bar & Line charts showing spending history over the last 6 months.
3. **Payment Method Share**: Pie chart showing usage across Cash, Cards, and Online transfers.

---

## 7. Testing & Verification

The project includes an automated test suite in `test_app.py` executed with Python's built-in `unittest` module:
- Verified user registration and session login.
- Verified expense creation, editing, filtering, and deletion.
- Verified budget threshold calculations and warning flags.
- Verified CSV and JSON export routes returning valid headers and data.
- Verified forgot password token generation.

---

## 8. Step-by-Step Implementation Log

1. **Environment Verification**: Checked Python 3.11.9 and Flask 3.1.3 availability.
2. **Database Engine Design (`models.py`)**: Built JSON file read/write logic, atomic file savers, user authentication helpers, and expense/budget query functions.
3. **Flask Routing & Controllers (`app.py`)**: Implemented all page routes, session handlers, filter pipelines, budget calculations, and export endpoints.
4. **CSS & JS Design (`static/css/style.css`, `static/js/main.js`)**: Designed a responsive UI with custom CSS variables, accessible typography, responsive grid layouts, mobile navigation, and flash dismissal.
5. **Jinja2 Templates (`templates/`)**: Built templates for base layout, landing page, auth (login, signup, forgot/reset password), dashboard, expense CRUD, budget, analytics, profile, and 404/500 errors.
6. **Automated Testing (`test_app.py`)**: Created and ran full test coverage with 100% pass rate.
7. **Demo Seeder (`seed_demo_data.py`)**: Created an interactive data generator to bootstrap sample expenses and demo user credentials (`demo` / `password123`).
8. **Documentation**: Created `README.md`, `PROJECT_DOCUMENTATION.md`, and walkthrough artifact.
