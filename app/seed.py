"""Fills a fresh database with demo data: one user, 8 categories,
about 50 expenses over 3 months, and a few budgets.

Run with:  flask --app app seed
"""

import calendar
import random
from datetime import date

from werkzeug.security import generate_password_hash

from app import queries

DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo12345"

NOTES = {
    "Food": ["Canteen lunch", "Chai and samosa", "Mess dinner", "Sweets for the lab"],
    "Travel": ["Auto fare to college", "Bus pass recharge", "Train ticket home", "Metro ride"],
    "Groceries": ["Milk and bread", "Vegetables", "Rice and dal", "Cleaning soap"],
    "Rent": ["Room rent share"],
    "Utilities": ["Electricity bill", "Mobile recharge", "Internet bill"],
    "Stationery": ["Xerox of assignment", "Notebook and pen", "Printer cartridge"],
    "Health": ["Pharmacy", "Doctor visit"],
    "Entertainment": ["Movie ticket", "Coffee with project group", "Cricket match entry"],
}

# Deliberately a little tight so the demo shows ochre and brick bars.
BUDGETS = {"Food": 3500, "Travel": 1400, "Groceries": 2600, "Utilities": 1500}
METHODS = ["cash", "UPI", "card", "bank"]


def month_key(year, month, delta):
    month += delta
    year += (month - 1) // 12
    month = (month - 1) % 12 + 1
    return year, month


def last_month_keys(count, today=None):
    today = today or date.today()
    keys = []
    year, month = today.year, today.month
    for _ in range(count):
        keys.append((year, month))
        year, month = month_key(year, month, -1)
    return keys


def populate_demo_data(user_id):
    """Fills one existing user with the canonical demo data. Call inside an app context."""
    queries.create_default_categories(user_id)
    categories = queries.list_categories(user_id)
    by_name = {c["name"]: c for c in categories}

    random.seed(11)
    today = date.today()
    added = 0
    for year, month in last_month_keys(3, today):
        last_day = calendar.monthrange(year, month)[1]
        if (year, month) == (today.year, today.month):
            last_day = today.day
        picks = random.sample(categories, 6)
        for _ in range(17):
            category = random.choice(picks)
            day = random.randint(1, last_day)
            amount = round(random.uniform(45, 1450) / 5) * 5
            queries.insert_expense(
                user_id,
                {
                    "category_id": category["id"],
                    "amount": float(amount),
                    "date": f"{year:04d}-{month:02d}-{day:02d}",
                    "payment_method": random.choice(METHODS),
                    "note": random.choice(NOTES[category["name"]]),
                },
            )
            added += 1

    for name, amount in BUDGETS.items():
        for year, month in last_month_keys(3, today):
            queries.set_budget(user_id, by_name[name]["id"], f"{year:04d}-{month:02d}", float(amount))

    budget_count = len(BUDGETS) * len(last_month_keys(3, today))
    return f"demo user, {len(categories)} categories, {added} expenses, {budget_count} budgets"


def seed_demo_user():
    """Returns (created, note). Runs inside an application context."""
    existing = queries.get_user_by_username(DEMO_USERNAME)
    if existing:
        return False, f"{DEMO_USERNAME} already exists, nothing added. Use 'flask --app app reseed-demo' to restore the demo data."

    user_id = queries.create_user(DEMO_USERNAME, generate_password_hash(DEMO_PASSWORD))
    return True, populate_demo_data(user_id)


def reseed_demo_user():
    """Restores only the demo account. Other users are left untouched."""
    from app.db import get_db

    existing = queries.get_user_by_username(DEMO_USERNAME)
    if not existing:
        return seed_demo_user()

    db = get_db()
    with db:
        db.execute("DELETE FROM expenses WHERE user_id = ?", (existing["id"],))
        db.execute("DELETE FROM budgets WHERE user_id = ?", (existing["id"],))
        db.execute("DELETE FROM categories WHERE user_id = ?", (existing["id"],))

    return True, "Demo data restored. " + populate_demo_data(existing["id"])


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        created, message = seed_demo_user()
    print(message)
