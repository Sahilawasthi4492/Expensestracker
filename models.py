"""
models.py - JSON Database Storage and Data Access Layer
This module handles reading and writing data to JSON files:
  - data/users.json: Stores user account details, hashed passwords, and password reset tokens.
  - data/expenses.json: Stores expense records and monthly budget limits for each user.
"""

import json
import os
import secrets
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

# Define base paths for data storage
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
EXPENSES_FILE = os.path.join(DATA_DIR, 'expenses.json')

def ensure_data_directory():
    """Ensure that data directory and required JSON files exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=4)

    if not os.path.exists(EXPENSES_FILE):
        with open(EXPENSES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"expenses": [], "budgets": {}}, f, indent=4)

def read_json_file(file_path, default_data):
    """Safely read and parse a JSON file."""
    ensure_data_directory()
    if not os.path.exists(file_path):
        return default_data
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default_data

def write_json_file(file_path, data):
    """Safely write data to a JSON file with pretty formatting."""
    ensure_data_directory()
    temp_file = file_path + '.tmp'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        # Atomic replace on same filesystem
        os.replace(temp_file, file_path)
        return True
    except Exception as e:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
        raise e


# ==========================================
# USER MANAGEMENT FUNCTIONS (data/users.json)
# ==========================================

def get_all_users():
    """Return all users from the JSON database."""
    return read_json_file(USERS_FILE, [])

def save_all_users(users):
    """Save user list to users.json."""
    return write_json_file(USERS_FILE, users)

def get_user_by_id(user_id):
    """Find a user by unique ID."""
    users = get_all_users()
    for user in users:
        if user.get('id') == str(user_id):
            return user
    return None

def get_user_by_email(email):
    """Find a user by email (case-insensitive)."""
    if not email:
        return None
    users = get_all_users()
    email_clean = email.strip().lower()
    for user in users:
        if user.get('email', '').strip().lower() == email_clean:
            return user
    return None

def get_user_by_username(username):
    """Find a user by username (case-insensitive)."""
    if not username:
        return None
    users = get_all_users()
    uname_clean = username.strip().lower()
    for user in users:
        if user.get('username', '').strip().lower() == uname_clean:
            return user
    return None

def create_user(full_name, username, email, password, currency='$'):
    """Create a new user record with hashed password."""
    users = get_all_users()

    # Generate a unique integer or string ID
    next_id = 1
    if users:
        existing_ids = [int(u['id']) for u in users if str(u.get('id', '')).isdigit()]
        if existing_ids:
            next_id = max(existing_ids) + 1

    hashed_password = generate_password_hash(password, method='scrypt')

    new_user = {
        'id': str(next_id),
        'full_name': full_name.strip(),
        'username': username.strip(),
        'email': email.strip().lower(),
        'password_hash': hashed_password,
        'currency': currency or '$',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'reset_token': None,
        'reset_token_expires': None
    }

    users.append(new_user)
    save_all_users(users)
    return new_user

def verify_user_password(user, password):
    """Check if provided plain password matches stored hash."""
    if not user or 'password_hash' not in user:
        return False
    return check_password_hash(user['password_hash'], password)

def update_user_password(user_id, new_password):
    """Update user's password with new hash."""
    users = get_all_users()
    for user in users:
        if user.get('id') == str(user_id):
            user['password_hash'] = generate_password_hash(new_password, method='scrypt')
            user['reset_token'] = None
            user['reset_token_expires'] = None
            save_all_users(users)
            return True
    return False

def update_user_profile(user_id, full_name, email, currency):
    """Update profile information for user."""
    users = get_all_users()
    for user in users:
        if user.get('id') == str(user_id):
            user['full_name'] = full_name.strip()
            user['email'] = email.strip().lower()
            user['currency'] = currency.strip()
            save_all_users(users)
            return True
    return False

def generate_reset_token(email):
    """Generate a secure password reset token valid for 1 hour."""
    users = get_all_users()
    email_clean = email.strip().lower()
    for user in users:
        if user.get('email', '').strip().lower() == email_clean:
            # Generate 32-character random token
            token = secrets.token_urlsafe(32)
            expiry = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            user['reset_token'] = token
            user['reset_token_expires'] = expiry
            save_all_users(users)
            return token, user
    return None, None

def verify_reset_token(token):
    """Verify if reset token exists and has not expired."""
    if not token:
        return None
    users = get_all_users()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    for user in users:
        if user.get('reset_token') == token:
            expires = user.get('reset_token_expires')
            if expires and expires >= now_str:
                return user
    return None

def reset_password_with_token(token, new_password):
    """Reset password using a valid token."""
    user = verify_reset_token(token)
    if not user:
        return False
    return update_user_password(user['id'], new_password)


# ===============================================
# EXPENSES & BUDGET MANAGEMENT (data/expenses.json)
# ===============================================

CATEGORIES = [
    'Food & Dining',
    'Shopping',
    'Transportation',
    'Housing & Rent',
    'Utilities & Bills',
    'Entertainment',
    'Healthcare & Fitness',
    'Education',
    'Personal Care',
    'Travel',
    'Investments',
    'Other'
]

PAYMENT_METHODS = [
    'Cash',
    'Credit Card',
    'Debit Card',
    'UPI / Online',
    'Bank Transfer',
    'Digital Wallet',
    'Other'
]

def get_expense_data():
    """Read all expense data including budgets dictionary."""
    return read_json_file(EXPENSES_FILE, {"expenses": [], "budgets": {}})

def save_expense_data(data):
    """Save expense and budget data to expenses.json."""
    return write_json_file(EXPENSES_FILE, data)

def get_user_expenses(user_id, category=None, payment_method=None, start_date=None, end_date=None, search=None, sort_by='date_desc'):
    """
    Query and filter expense records for a specific user.
    Supports filtering by category, payment method, date range, search keyword, and sorting.
    """
    data = get_expense_data()
    all_expenses = data.get('expenses', [])
    user_id_str = str(user_id)

    # Filter by user ID
    user_records = [exp for exp in all_expenses if str(exp.get('user_id')) == user_id_str]

    # Filter by category
    if category and category != 'All':
        user_records = [exp for exp in user_records if exp.get('category') == category]

    # Filter by payment method
    if payment_method and payment_method != 'All':
        user_records = [exp for exp in user_records if exp.get('payment_method') == payment_method]

    # Filter by start date
    if start_date:
        user_records = [exp for exp in user_records if exp.get('date') >= start_date]

    # Filter by end date
    if end_date:
        user_records = [exp for exp in user_records if exp.get('date') <= end_date]

    # Filter by search keyword (searches in title, notes, and tags)
    if search:
        s = search.strip().lower()
        user_records = [
            exp for exp in user_records
            if s in exp.get('title', '').lower()
            or s in exp.get('notes', '').lower()
            or s in exp.get('category', '').lower()
            or s in exp.get('payment_method', '').lower()
            or any(s in tag.lower() for tag in exp.get('tags', []))
        ]

    # Sort results
    if sort_by == 'date_asc':
        user_records.sort(key=lambda x: (x.get('date', ''), x.get('created_at', '')))
    elif sort_by == 'amount_desc':
        user_records.sort(key=lambda x: float(x.get('amount', 0)), reverse=True)
    elif sort_by == 'amount_asc':
        user_records.sort(key=lambda x: float(x.get('amount', 0)))
    else:  # 'date_desc' (default)
        user_records.sort(key=lambda x: (x.get('date', ''), x.get('created_at', '')), reverse=True)

    return user_records

def get_expense_by_id(expense_id, user_id=None):
    """Fetch single expense item by ID, optionally verifying ownership."""
    data = get_expense_data()
    for exp in data.get('expenses', []):
        if str(exp.get('id')) == str(expense_id):
            if user_id is None or str(exp.get('user_id')) == str(user_id):
                return exp
    return None

def add_expense(user_id, title, amount, category, date, payment_method='Cash', notes='', tags=None):
    """Add a new expense record to the JSON database."""
    data = get_expense_data()
    expenses = data.get('expenses', [])

    next_id = 1
    if expenses:
        existing_ids = [int(e['id']) for e in expenses if str(e.get('id', '')).isdigit()]
        if existing_ids:
            next_id = max(existing_ids) + 1

    if tags is None:
        tags = []
    elif isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]

    new_expense = {
        'id': str(next_id),
        'user_id': str(user_id),
        'title': title.strip(),
        'amount': round(float(amount), 2),
        'category': category if category in CATEGORIES else 'Other',
        'date': date,
        'payment_method': payment_method if payment_method in PAYMENT_METHODS else 'Other',
        'notes': notes.strip(),
        'tags': tags,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    expenses.append(new_expense)
    data['expenses'] = expenses
    save_expense_data(data)
    return new_expense

def update_expense(expense_id, user_id, title, amount, category, date, payment_method='Cash', notes='', tags=None):
    """Update an existing expense record."""
    data = get_expense_data()
    expenses = data.get('expenses', [])

    if tags is None:
        tags = []
    elif isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',') if t.strip()]

    for exp in expenses:
        if str(exp.get('id')) == str(expense_id) and str(exp.get('user_id')) == str(user_id):
            exp['title'] = title.strip()
            exp['amount'] = round(float(amount), 2)
            exp['category'] = category if category in CATEGORIES else 'Other'
            exp['date'] = date
            exp['payment_method'] = payment_method if payment_method in PAYMENT_METHODS else 'Other'
            exp['notes'] = notes.strip()
            exp['tags'] = tags
            exp['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_expense_data(data)
            return exp
    return None

def delete_expense(expense_id, user_id):
    """Delete an expense record."""
    data = get_expense_data()
    expenses = data.get('expenses', [])
    initial_len = len(expenses)

    new_expenses = [
        exp for exp in expenses
        if not (str(exp.get('id')) == str(expense_id) and str(exp.get('user_id')) == str(user_id))
    ]

    if len(new_expenses) < initial_len:
        data['expenses'] = new_expenses
        save_expense_data(data)
        return True
    return False

# ==========================================
# BUDGET AND SUMMARY METRICS
# ==========================================

def get_user_budget(user_id, month=None):
    """
    Get the monthly budget set by user.
    month format: 'YYYY-MM'. If None, uses current month.
    """
    if month is None:
        month = datetime.now().strftime('%Y-%m')
    data = get_expense_data()
    budgets = data.get('budgets', {})
    user_budgets = budgets.get(str(user_id), {})
    return float(user_budgets.get(month, user_budgets.get('default', 0.0)))

def set_user_budget(user_id, amount, month=None):
    """Set monthly budget limit for user."""
    if month is None:
        month = datetime.now().strftime('%Y-%m')
    data = get_expense_data()
    if 'budgets' not in data:
        data['budgets'] = {}
    if str(user_id) not in data['budgets']:
        data['budgets'][str(user_id)] = {}

    data['budgets'][str(user_id)][month] = round(float(amount), 2)
    data['budgets'][str(user_id)]['default'] = round(float(amount), 2)
    save_expense_data(data)
    return True

def get_expense_summary(user_id, month=None):
    """
    Calculate comprehensive analytics for user:
      - Total all-time spend
      - Current month spend
      - Today spend
      - Budget and remaining budget
      - Category breakdown (totals & percentages)
      - Payment method breakdown
      - Recent 6 months spending trends
    """
    if month is None:
        month = datetime.now().strftime('%Y-%m')

    today_str = datetime.now().strftime('%Y-%m-%d')
    all_expenses = get_user_expenses(user_id, sort_by='date_desc')

    total_all_time = sum(float(e['amount']) for e in all_expenses)

    # Monthly expenses
    monthly_expenses = [e for e in all_expenses if e.get('date', '').startswith(month)]
    total_this_month = sum(float(e['amount']) for e in monthly_expenses)

    # Today expenses
    today_expenses = [e for e in all_expenses if e.get('date') == today_str]
    total_today = sum(float(e['amount']) for e in today_expenses)

    # Budget info
    budget = get_user_budget(user_id, month)
    remaining_budget = budget - total_this_month if budget > 0 else 0
    budget_usage_percent = round((total_this_month / budget * 100), 1) if budget > 0 else 0

    # Category breakdown (for current month and all time)
    category_totals = {}
    for cat in CATEGORIES:
        category_totals[cat] = 0.0

    for exp in monthly_expenses:
        cat = exp.get('category', 'Other')
        category_totals[cat] = category_totals.get(cat, 0.0) + float(exp['amount'])

    # Filter out 0 categories for chart clarity
    active_categories = {k: round(v, 2) for k, v in category_totals.items() if v > 0}

    # Payment method breakdown
    payment_totals = {}
    for exp in monthly_expenses:
        pm = exp.get('payment_method', 'Other')
        payment_totals[pm] = payment_totals.get(pm, 0.0) + float(exp['amount'])
    active_payments = {k: round(v, 2) for k, v in payment_totals.items() if v > 0}

    # Monthly Trends (last 6 months)
    monthly_trends = {}
    curr_date = datetime.now()
    for i in range(5, -1, -1):
        # Calculate year and month
        y = curr_date.year
        m = curr_date.month - i
        while m <= 0:
            m += 12
            y -= 1
        m_str = f"{y:04d}-{m:02d}"
        m_label = datetime(y, m, 1).strftime('%b %Y')
        m_total = sum(float(e['amount']) for e in all_expenses if e.get('date', '').startswith(m_str))
        monthly_trends[m_label] = round(m_total, 2)

    return {
        'total_all_time': round(total_all_time, 2),
        'total_this_month': round(total_this_month, 2),
        'total_today': round(total_today, 2),
        'transaction_count': len(all_expenses),
        'month_transaction_count': len(monthly_expenses),
        'budget': budget,
        'remaining_budget': round(remaining_budget, 2),
        'budget_usage_percent': budget_usage_percent,
        'category_breakdown': active_categories,
        'payment_breakdown': active_payments,
        'monthly_trends': monthly_trends,
        'current_month_name': datetime.strptime(month, '%Y-%m').strftime('%B %Y')
    }

# Initialize data directories and files on import
ensure_data_directory()
