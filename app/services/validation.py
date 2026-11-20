"""Turning form data into cleaned values, or into field errors.

No Flask import here, so the unit tests do not need an app.
"""

import math
from datetime import datetime

PAYMENT_METHODS = ["cash", "UPI", "card", "bank"]

MAX_AMOUNT = 99999999.99
DATE_FORMAT = "%Y-%m-%d"
DATE_MIN = datetime(2000, 1, 1)
DATE_MAX = datetime(2100, 12, 31)


def validate_amount(raw):
    text = (raw or "").strip().replace(",", "")
    if not text:
        return None, "Amount is required"
    try:
        value = float(text)
    except ValueError:
        return None, "Amount must be a number"
    if not math.isfinite(value):
        return None, "Amount must be a number"
    # Check the value that will actually be stored: 0.004 rounds to 0.00,
    # which SQLite rejects because the column requires amount > 0.
    value = round(value, 2)
    if value <= 0:
        return None, "Amount must be more than 0"
    if value > MAX_AMOUNT:
        return None, "Amount is too large"
    return value, None


def validate_date(raw):
    text = (raw or "").strip()
    if not text:
        return None, "Date is required"
    try:
        parsed = datetime.strptime(text, DATE_FORMAT)
    except ValueError:
        return None, "Use the date format YYYY-MM-DD"
    if not (DATE_MIN <= parsed <= DATE_MAX):
        return None, "Date must be between 2000-01-01 and 2100-12-31"
    return parsed.date().isoformat(), None


def validate_note(raw):
    text = (raw or "").strip()
    if len(text) > 200:
        return None, "Note is too long, 200 characters maximum"
    return text, None


def validate_payment_method(raw):
    text = (raw or "").strip()
    if text not in PAYMENT_METHODS:
        return None, "Choose a payment method"
    return text, None


def validate_category(raw, categories):
    """categories is the list of dicts the user owns."""
    try:
        wanted = int(raw)
    except (TypeError, ValueError):
        return None, "Choose a category"
    for category in categories:
        if category["id"] == wanted:
            return wanted, None
    return None, "Choose a category"


def validate_expense(form, categories):
    """Returns (data, errors). data is usable only when errors is empty."""
    errors = {}
    data = {}

    data["amount"], err = validate_amount(form.get("amount"))
    if err:
        errors["amount"] = err

    data["date"], err = validate_date(form.get("date"))
    if err:
        errors["date"] = err

    data["category_id"], err = validate_category(form.get("category_id"), categories)
    if err:
        errors["category_id"] = err

    data["payment_method"], err = validate_payment_method(form.get("payment_method"))
    if err:
        errors["payment_method"] = err

    data["note"], err = validate_note(form.get("note"))
    if err:
        errors["note"] = err

    return data, errors


def validate_register(username, password, confirm):
    errors = {}
    name = (username or "").strip()
    if not name:
        errors["username"] = "Username is required"
    elif len(name) < 3:
        errors["username"] = "Username needs at least 3 characters"
    elif len(name) > 40:
        errors["username"] = "Username is too long"
    if not password:
        errors["password"] = "Password is required"
    elif len(password) < 8:
        errors["password"] = "Password needs at least 8 characters"
    elif password != confirm:
        errors["confirm"] = "The two passwords do not match"
    return name, errors


def validate_login(username, password):
    errors = {}
    if not (username or "").strip():
        errors["username"] = "Username is required"
    if not password:
        errors["password"] = "Password is required"
    return errors


def validate_password_change(current, new, confirm):
    errors = {}
    if not current:
        errors["current"] = "Enter your current password"
    if not new:
        errors["new"] = "Enter a new password"
    elif len(new) < 8:
        errors["new"] = "Password needs at least 8 characters"
    elif new != confirm:
        errors["confirm"] = "The two passwords do not match"
    return errors


def validate_category_name(name, taken_names):
    text = (name or "").strip()
    if not text:
        return None, "Category name is required"
    if len(text) > 40:
        return None, "Category name is too long"
    if text.lower() in {n.lower() for n in taken_names}:
        return None, "You already have a category with this name"
    return text, None


def validate_budget_amount(raw):
    text = (raw or "").strip().replace(",", "")
    if not text:
        return None, "Budget amount is required"
    try:
        value = float(text)
    except ValueError:
        return None, "Budget amount must be a number"
    if not math.isfinite(value):
        return None, "Budget amount must be a number"
    value = round(value, 2)
    if value <= 0:
        return None, "Budget must be more than 0"
    if value > MAX_AMOUNT:
        return None, "Budget is too large"
    return value, None
