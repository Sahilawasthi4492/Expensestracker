"""
app.py - Main Flask Web Application for Personal Expense Tracker
Handles application configuration, routing, session authentication,
expense CRUD operations, analytics, budget alerts, and data exports.
"""

import os
import io
import csv
import json
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, make_response, jsonify
)

import models

# Initialize Flask application
app = Flask(__name__)

# Secret key for session signing and flash messages
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'personal-expense-tracker-secret-key-2026')


# ==========================================
# AUTHENTICATION HELPERS & DECORATORS
# ==========================================

def login_required(f):
    """Decorator to protect routes requiring user authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.context_processor
def inject_global_variables():
    """Make user data and constants available in all templates."""
    current_user = None
    if 'user_id' in session:
        current_user = models.get_user_by_id(session['user_id'])
    
    return {
        'current_user': current_user,
        'CATEGORIES': models.CATEGORIES,
        'PAYMENT_METHODS': models.PAYMENT_METHODS,
        'now_year': datetime.now().year,
        'today_date': datetime.now().strftime('%Y-%m-%d')
    }


# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/')
def index():
    """Landing page or redirect to dashboard if logged in."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handle new user registration."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        currency = request.form.get('currency', '$').strip() or '$'

        # Validation
        if not full_name or not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('auth/signup.html', full_name=full_name, username=username, email=email, currency=currency)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/signup.html', full_name=full_name, username=username, email=email, currency=currency)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/signup.html', full_name=full_name, username=username, email=email, currency=currency)

        # Check existing user
        if models.get_user_by_email(email):
            flash('An account with this email already exists.', 'danger')
            return render_template('auth/signup.html', full_name=full_name, username=username, currency=currency)

        if models.get_user_by_username(username):
            flash('Username is already taken. Please choose another.', 'danger')
            return render_template('auth/signup.html', full_name=full_name, email=email, currency=currency)

        # Create user
        user = models.create_user(full_name, username, email, password, currency)
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login and session creation."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember')

        if not identifier or not password:
            flash('Please enter both email/username and password.', 'danger')
            return render_template('auth/login.html', identifier=identifier)

        # Allow login via Email or Username
        user = models.get_user_by_email(identifier) or models.get_user_by_username(identifier)

        if not user or not models.verify_user_password(user, password):
            flash('Invalid email/username or password.', 'danger')
            return render_template('auth/login.html', identifier=identifier)

        # Set session
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session.permanent = bool(remember)

        flash(f"Welcome back, {user.get('full_name') or user.get('username')}!", 'success')
        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('dashboard'))

    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    """Clear session and log user out."""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Handle password reset request by generating a reset token."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash('Please provide your registered email address.', 'danger')
            return render_template('auth/forgot_password.html')

        token, user = models.generate_reset_token(email)
        if user:
            # Generate simulated reset link
            reset_url = url_for('reset_password', token=token, _external=True)
            return render_template('auth/forgot_password.html', reset_url=reset_url, email=email, token_generated=True)
        else:
            # For security, standard message or warning
            flash('If an account exists with that email, a password reset link has been prepared.', 'info')
            return render_template('auth/forgot_password.html')

    return render_template('auth/forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle setting a new password via valid reset token."""
    user = models.verify_reset_token(token)
    if not user:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if models.reset_password_with_token(token, password):
            flash('Your password has been updated successfully! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Failed to reset password. Token might be expired.', 'danger')
            return redirect(url_for('forgot_password'))

    return render_template('auth/reset_password.html', token=token, email=user.get('email'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update user profile & password."""
    user = models.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            currency = request.form.get('currency', '$').strip() or '$'

            if not full_name or not email:
                flash('Name and email are required.', 'danger')
                return render_template('profile.html', user=user)

            # Check if email taken by someone else
            existing = models.get_user_by_email(email)
            if existing and existing['id'] != user['id']:
                flash('Email is already in use by another account.', 'danger')
                return render_template('profile.html', user=user)

            models.update_user_profile(user['id'], full_name, email, currency)
            flash('Profile updated successfully!', 'success')
            user = models.get_user_by_id(session['user_id'])

        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new_password = request.form.get('confirm_new_password', '')

            if not models.verify_user_password(user, current_password):
                flash('Current password is incorrect.', 'danger')
                return render_template('profile.html', user=user)

            if len(new_password) < 6:
                flash('New password must be at least 6 characters.', 'danger')
                return render_template('profile.html', user=user)

            if new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
                return render_template('profile.html', user=user)

            models.update_user_password(user['id'], new_password)
            flash('Password changed successfully!', 'success')

    return render_template('profile.html', user=user)


# ==========================================
# DASHBOARD & CORE EXPENSE MANAGEMENT
# ==========================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard displaying summary statistics, budget progress, charts, and recent expenses."""
    user_id = session['user_id']
    user = models.get_user_by_id(user_id)
    summary = models.get_expense_summary(user_id)
    recent_expenses = models.get_user_expenses(user_id, sort_by='date_desc')[:6]

    # JSON for Chart.js rendering
    category_labels = list(summary['category_breakdown'].keys())
    category_values = list(summary['category_breakdown'].values())
    trend_labels = list(summary['monthly_trends'].keys())
    trend_values = list(summary['monthly_trends'].values())

    return render_template(
        'dashboard.html',
        user=user,
        summary=summary,
        recent_expenses=recent_expenses,
        category_labels_json=json.dumps(category_labels),
        category_values_json=json.dumps(category_values),
        trend_labels_json=json.dumps(trend_labels),
        trend_values_json=json.dumps(trend_values)
    )


@app.route('/expenses')
@login_required
def expense_list():
    """View, search, filter, and sort expense records."""
    user_id = session['user_id']
    category = request.args.get('category', 'All')
    payment_method = request.args.get('payment_method', 'All')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort_by', 'date_desc')

    expenses = models.get_user_expenses(
        user_id=user_id,
        category=category,
        payment_method=payment_method,
        start_date=start_date,
        end_date=end_date,
        search=search,
        sort_by=sort_by
    )

    filtered_total = sum(float(e['amount']) for e in expenses)

    return render_template(
        'expenses/list.html',
        expenses=expenses,
        filtered_total=round(filtered_total, 2),
        selected_category=category,
        selected_payment=payment_method,
        start_date=start_date,
        end_date=end_date,
        search=search,
        sort_by=sort_by
    )


@app.route('/expenses/add', methods=['GET', 'POST'])
@login_required
def add_expense_route():
    """Add a new expense item."""
    user_id = session['user_id']
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        amount = request.form.get('amount', '').strip()
        category = request.form.get('category', '')
        date = request.form.get('date', '').strip()
        payment_method = request.form.get('payment_method', 'Cash')
        notes = request.form.get('notes', '').strip()
        tags = request.form.get('tags', '').strip()

        if not title or not amount or not date or not category:
            flash('Title, amount, date, and category are required.', 'danger')
            return render_template(
                'expenses/add.html',
                title=title,
                amount=amount,
                category=category,
                date=date,
                payment_method=payment_method,
                notes=notes,
                tags=tags
            )

        try:
            val_amount = float(amount)
            if val_amount <= 0:
                raise ValueError()
        except ValueError:
            flash('Amount must be a valid positive number.', 'danger')
            return render_template(
                'expenses/add.html',
                title=title,
                amount=amount,
                category=category,
                date=date,
                payment_method=payment_method,
                notes=notes,
                tags=tags
            )

        models.add_expense(
            user_id=user_id,
            title=title,
            amount=val_amount,
            category=category,
            date=date,
            payment_method=payment_method,
            notes=notes,
            tags=tags
        )

        flash('Expense added successfully!', 'success')
        return redirect(url_for('expense_list'))

    return render_template('expenses/add.html', default_date=datetime.now().strftime('%Y-%m-%d'))


@app.route('/expenses/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
def edit_expense_route(expense_id):
    """Edit an existing expense item."""
    user_id = session['user_id']
    expense = models.get_expense_by_id(expense_id, user_id=user_id)
    if not expense:
        flash('Expense not found or unauthorized access.', 'danger')
        return redirect(url_for('expense_list'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        amount = request.form.get('amount', '').strip()
        category = request.form.get('category', '')
        date = request.form.get('date', '').strip()
        payment_method = request.form.get('payment_method', 'Cash')
        notes = request.form.get('notes', '').strip()
        tags = request.form.get('tags', '').strip()

        if not title or not amount or not date or not category:
            flash('Title, amount, date, and category are required.', 'danger')
            return render_template('expenses/edit.html', expense=expense)

        try:
            val_amount = float(amount)
            if val_amount <= 0:
                raise ValueError()
        except ValueError:
            flash('Amount must be a valid positive number.', 'danger')
            return render_template('expenses/edit.html', expense=expense)

        models.update_expense(
            expense_id=expense_id,
            user_id=user_id,
            title=title,
            amount=val_amount,
            category=category,
            date=date,
            payment_method=payment_method,
            notes=notes,
            tags=tags
        )

        flash('Expense updated successfully!', 'success')
        return redirect(url_for('expense_list'))

    tags_str = ', '.join(expense.get('tags', []))
    return render_template('expenses/edit.html', expense=expense, tags_str=tags_str)


@app.route('/expenses/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense_route(expense_id):
    """Delete an expense item."""
    user_id = session['user_id']
    if models.delete_expense(expense_id, user_id=user_id):
        flash('Expense deleted successfully!', 'success')
    else:
        flash('Failed to delete expense or item not found.', 'danger')
    return redirect(url_for('expense_list'))


# ==========================================
# BUDGETING & ANALYTICS
# ==========================================

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget_route():
    """Set and view monthly budgets and spending limits."""
    user_id = session['user_id']
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))

    if request.method == 'POST':
        budget_amount = request.form.get('budget_amount', '').strip()
        month_to_set = request.form.get('month', selected_month)

        try:
            amt = float(budget_amount)
            if amt < 0:
                raise ValueError()
            models.set_user_budget(user_id, amt, month=month_to_set)
            flash(f"Monthly budget updated to {amt:.2f} successfully!", 'success')
            return redirect(url_for('budget_route', month=month_to_set))
        except ValueError:
            flash('Please enter a valid non-negative budget amount.', 'danger')

    summary = models.get_expense_summary(user_id, month=selected_month)
    return render_template('budget.html', summary=summary, selected_month=selected_month)


@app.route('/analytics')
@login_required
def analytics_route():
    """Visual graphs and spending breakdowns across categories, payments, and time."""
    user_id = session['user_id']
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    summary = models.get_expense_summary(user_id, month=selected_month)

    category_labels = list(summary['category_breakdown'].keys())
    category_values = list(summary['category_breakdown'].values())
    payment_labels = list(summary['payment_breakdown'].keys())
    payment_values = list(summary['payment_breakdown'].values())
    trend_labels = list(summary['monthly_trends'].keys())
    trend_values = list(summary['monthly_trends'].values())

    return render_template(
        'analytics.html',
        summary=summary,
        selected_month=selected_month,
        category_labels_json=json.dumps(category_labels),
        category_values_json=json.dumps(category_values),
        payment_labels_json=json.dumps(payment_labels),
        payment_values_json=json.dumps(payment_values),
        trend_labels_json=json.dumps(trend_labels),
        trend_values_json=json.dumps(trend_values)
    )


# ==========================================
# DATA EXPORT ROUTES
# ==========================================

@app.route('/export/csv')
@login_required
def export_csv():
    """Export expenses as a downloadable CSV spreadsheet."""
    user_id = session['user_id']
    category = request.args.get('category', 'All')
    payment_method = request.args.get('payment_method', 'All')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    search = request.args.get('search', '')

    expenses = models.get_user_expenses(
        user_id=user_id,
        category=category,
        payment_method=payment_method,
        start_date=start_date,
        end_date=end_date,
        search=search,
        sort_by='date_desc'
    )

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['ID', 'Date', 'Title', 'Category', 'Amount', 'Payment Method', 'Tags', 'Notes'])

    for exp in expenses:
        writer.writerow([
            exp.get('id'),
            exp.get('date'),
            exp.get('title'),
            exp.get('category'),
            f"{float(exp.get('amount', 0)):.2f}",
            exp.get('payment_method'),
            ', '.join(exp.get('tags', [])),
            exp.get('notes')
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output


@app.route('/export/json')
@login_required
def export_json():
    """Export user's expenses in JSON format."""
    user_id = session['user_id']
    expenses = models.get_user_expenses(user_id=user_id, sort_by='date_desc')
    user = models.get_user_by_id(user_id)

    export_payload = {
        'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user': {
            'username': user.get('username'),
            'email': user.get('email'),
            'currency': user.get('currency')
        },
        'total_expenses_count': len(expenses),
        'total_amount': sum(float(e['amount']) for e in expenses),
        'expenses': expenses
    }

    json_str = json.dumps(export_payload, indent=4, ensure_ascii=False)
    output = make_response(json_str)
    output.headers["Content-Disposition"] = f"attachment; filename=expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output.headers["Content-type"] = "application/json; charset=utf-8"
    return output


# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500


if __name__ == '__main__':
    # Ensure data storage is ready
    models.ensure_data_directory()
    print(" * Personal Expense Tracker is running on http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
