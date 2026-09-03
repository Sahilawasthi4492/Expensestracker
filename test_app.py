"""
test_app.py - Automated Test Suite for Personal Expense Tracker
Tests all core authentication, CRUD operations, budgeting, filtering, and export endpoints.
"""

import os
import unittest
import json
import shutil
import tempfile

import models
from app import app

class ExpenseTrackerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary test data directory
        cls.test_dir = tempfile.mkdtemp()
        models.DATA_DIR = cls.test_dir
        models.USERS_FILE = os.path.join(cls.test_dir, 'users.json')
        models.EXPENSES_FILE = os.path.join(cls.test_dir, 'expenses.json')
        models.ensure_data_directory()

    @classmethod
    def tearDownClass(cls):
        # Remove temporary directory
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        self.client = app.test_client()

    def test_01_homepage(self):
        """Test landing page returns 200."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Personal Expense Tracker', response.data)

    def test_02_signup_and_login(self):
        """Test user registration and subsequent login."""
        # 1. Signup
        signup_res = self.client.post('/signup', data={
            'full_name': 'Test User',
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'currency': '$'
        }, follow_redirects=True)
        self.assertEqual(signup_res.status_code, 200)
        self.assertIn(b'Account created successfully', signup_res.data)

        # 2. Login
        login_res = self.client.post('/login', data={
            'identifier': 'testuser@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b'Welcome, Test User', login_res.data)

    def test_03_expense_crud_and_budget(self):
        """Test adding, editing, filtering, and deleting expenses as well as budget setting."""
        # Log in first
        self.client.post('/login', data={
            'identifier': 'testuser@example.com',
            'password': 'password123'
        }, follow_redirects=True)

        # 1. Add Expense
        add_res = self.client.post('/expenses/add', data={
            'title': 'Test Grocery',
            'amount': '125.50',
            'category': 'Food & Dining',
            'date': '2026-09-01',
            'payment_method': 'Credit Card',
            'notes': 'Supermarket fruits & vegetables',
            'tags': 'groceries, organic'
        }, follow_redirects=True)
        self.assertEqual(add_res.status_code, 200)
        self.assertIn(b'Expense added successfully', add_res.data)
        self.assertIn(b'Test Grocery', add_res.data)

        # 2. Add Second Expense
        self.client.post('/expenses/add', data={
            'title': 'Metro Pass',
            'amount': '45.00',
            'category': 'Transportation',
            'date': '2026-09-02',
            'payment_method': 'Cash',
            'notes': 'Monthly commute pass',
            'tags': 'transit'
        }, follow_redirects=True)

        # 3. Set Monthly Budget
        budget_res = self.client.post('/budget', data={
            'budget_amount': '500.00',
            'month': '2026-09'
        }, follow_redirects=True)
        self.assertEqual(budget_res.status_code, 200)
        self.assertIn(b'Monthly budget updated to 500.00 successfully', budget_res.data)

        # 4. View Expenses with filter
        filter_res = self.client.get('/expenses?category=Food%20%26%20Dining')
        self.assertEqual(filter_res.status_code, 200)
        self.assertIn(b'Test Grocery', filter_res.data)

        # 5. Export CSV
        csv_res = self.client.get('/export/csv')
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.content_type, 'text/csv; charset=utf-8')
        self.assertIn(b'Test Grocery', csv_res.data)

        # 6. Export JSON
        json_res = self.client.get('/export/json')
        self.assertEqual(json_res.status_code, 200)
        json_data = json.loads(json_res.data.decode('utf-8'))
        self.assertIn('expenses', json_data)
        self.assertGreaterEqual(len(json_data['expenses']), 2)

        # 7. Analytics page
        analytics_res = self.client.get('/analytics?month=2026-09')
        self.assertEqual(analytics_res.status_code, 200)
        self.assertIn(b'Analytics', analytics_res.data)

        # 8. Edit Expense
        edit_res = self.client.post('/expenses/edit/1', data={
            'title': 'Test Grocery Updated',
            'amount': '130.00',
            'category': 'Food & Dining',
            'date': '2026-09-01',
            'payment_method': 'Credit Card',
            'notes': 'Updated notes',
            'tags': 'groceries'
        }, follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)
        self.assertIn(b'Expense updated successfully', edit_res.data)

        # 9. Delete Expense
        del_res = self.client.post('/expenses/delete/1', follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertIn(b'Expense deleted successfully', del_res.data)

    def test_04_forgot_password_flow(self):
        """Test forgot password token generation."""
        res = self.client.post('/forgot-password', data={
            'email': 'testuser@example.com'
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'reset-password', res.data)

if __name__ == '__main__':
    unittest.main()
