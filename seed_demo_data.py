"""
seed_demo_data.py - Seed realistic sample data for demo purposes.
Creates a demo user (demo / password123) with varied expense records and a monthly budget.
"""

from datetime import datetime, timedelta
import models

def seed():
    models.ensure_data_directory()
    
    # Check if demo user already exists
    demo_user = models.get_user_by_username('demo')
    if not demo_user:
        demo_user = models.create_user(
            full_name="Alex Morgan",
            username="demo",
            email="demo@example.com",
            password="password123",
            currency="$"
        )
        print("[OK] Created Demo User: demo@example.com (Password: password123)")
    else:
        print("[OK] Demo User already exists.")

    uid = demo_user['id']
    now = datetime.now()
    curr_month_str = now.strftime('%Y-%m')

    # Set Monthly Budget
    models.set_user_budget(uid, 2500.00, month=curr_month_str)

    # Sample expenses
    sample_expenses = [
        ("Whole Foods Grocery Run", 142.80, "Food & Dining", now.strftime('%Y-%m-%d'), "Credit Card", "Fresh veggies, almond milk & snacks", ["groceries", "food"]),
        ("Metro Monthly Pass", 65.00, "Transportation", (now - timedelta(days=1)).strftime('%Y-%m-%d'), "Debit Card", "Public transit reload", ["commute"]),
        ("High-Speed Fiber Internet", 79.99, "Utilities & Bills", (now - timedelta(days=2)).strftime('%Y-%m-%d'), "UPI / Online", "Monthly fiber connection", ["utilities", "bills"]),
        ("Starbucks Coffee & Bagel", 12.45, "Food & Dining", (now - timedelta(days=3)).strftime('%Y-%m-%d'), "Cash", "Morning team breakfast", ["coffee"]),
        ("Movie Night Tickets", 34.50, "Entertainment", (now - timedelta(days=4)).strftime('%Y-%m-%d'), "Credit Card", "IMAX cinema with friends", ["movies", "weekend"]),
        ("Pharmacy & Vitamins", 28.75, "Healthcare & Fitness", (now - timedelta(days=5)).strftime('%Y-%m-%d'), "Debit Card", "Omega 3 & multivitamin supply", ["health"]),
        ("Casual Sneakers Sale", 89.90, "Shopping", (now - timedelta(days=7)).strftime('%Y-%m-%d'), "Credit Card", "Summer running shoes", ["apparel"]),
        ("Uber Ride to Airport", 42.10, "Transportation", (now - timedelta(days=10)).strftime('%Y-%m-%d'), "Digital Wallet", "Airport drop off", ["travel"]),
        ("Electricity Bill", 115.30, "Utilities & Bills", (now - timedelta(days=15)).strftime('%Y-%m-%d'), "Bank Transfer", "Power utility payment", ["utilities"]),
        ("Dinner with Colleagues", 95.00, "Food & Dining", (now - timedelta(days=18)).strftime('%Y-%m-%d'), "Credit Card", "Italian bistro dinner", ["dining"]),
    ]

    for title, amount, category, date, payment_method, notes, tags in sample_expenses:
        models.add_expense(
            user_id=uid,
            title=title,
            amount=amount,
            category=category,
            date=date,
            payment_method=payment_method,
            notes=notes,
            tags=tags
        )

    print(f"[OK] Added {len(sample_expenses)} sample transactions for {demo_user['username']}.")
    print("Seed complete! You can now log in with:")
    print("  Username: demo  (or demo@example.com)")
    print("  Password: password123")

if __name__ == '__main__':
    seed()
