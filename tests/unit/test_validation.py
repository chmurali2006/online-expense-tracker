from app.services.validation import (
    validate_amount,
    validate_budget_amount,
    validate_category_name,
    validate_date,
    validate_expense,
    validate_password_change,
)


def test_TC_001_amount_zero_rejected():
    value, error = validate_amount("0")
    assert value is None
    assert error == "Amount must be more than 0"


def test_TC_002_amount_one_paisa_accepted():
    value, error = validate_amount("0.01")
    assert value == 0.01
    assert error is None


def test_TC_003_amount_very_large_rejected():
    value, error = validate_amount("1000000000000")
    assert value is None
    assert error == "Amount is too large"


def test_TC_004_amount_negative_rejected():
    value, error = validate_amount("-45.50")
    assert value is None
    assert error == "Amount must be more than 0"


def test_TC_005_amount_non_numeric_rejected():
    value, error = validate_amount("abc")
    assert value is None
    assert error == "Amount must be a number"

    value, error = validate_amount("12.3.4")
    assert value is None


def test_TC_006_date_wrong_format_rejected():
    value, error = validate_date("31/02/2026")
    assert value is None
    assert error == "Use the date format YYYY-MM-DD"


def test_TC_007_date_out_of_range_rejected():
    value, error = validate_date("1999-05-05")
    assert value is None
    assert error == "Date must be between 2000-01-01 and 2100-12-31"

    value, error = validate_date("2026-13-01")
    assert value is None


def test_TC_008_register_password_too_short():
    from app.services.validation import validate_register

    _, errors = validate_register("riya", "short", "short")
    assert errors["password"] == "Password needs at least 8 characters"

    _, errors = validate_register("riya", "secret123", "other1234")
    assert errors["confirm"] == "The two passwords do not match"


def test_TC_009_duplicate_category_name_rejected():
    _, error = validate_category_name("Food", ["food", "Travel"])
    assert error == "You already have a category with this name"

    name, error = validate_category_name("Metro card", ["Food"])
    assert name == "Metro card"
    assert error is None


def test_TC_010_budget_amount_not_positive():
    value, error = validate_budget_amount("-100")
    assert value is None
    assert error == "Budget must be more than 0"

    value, error = validate_budget_amount("4000")
    assert value == 4000.0
    assert error is None


def test_expense_form_collects_field_errors():
    categories = [{"id": 1, "name": "Food"}]
    data, errors = validate_expense(
        {"amount": "0", "date": "nope", "category_id": "99", "payment_method": "cheque", "note": ""},
        categories,
    )
    assert set(errors) == {"amount", "date", "category_id", "payment_method"}
    assert data["amount"] is None

    data, errors = validate_expense(
        {"amount": "250", "date": "2026-03-04", "category_id": "1", "payment_method": "UPI", "note": "Chai"},
        categories,
    )
    assert errors == {}
    assert data == {
        "amount": 250.0,
        "date": "2026-03-04",
        "category_id": 1,
        "payment_method": "UPI",
        "note": "Chai",
    }


def test_non_finite_and_sub_paise_amounts_are_rejected():
    for raw in ("nan", "NaN", "inf", "-inf"):
        value, error = validate_amount(raw)
        assert value is None
        assert error is not None

    # These round to 0.00 and would be rejected by SQLite's CHECK (amount > 0).
    for raw in ("0.001", "0.004", "0.0001"):
        value, error = validate_amount(raw)
        assert value is None
        assert error == "Amount must be more than 0"


def test_non_finite_and_sub_paise_budgets_are_rejected():
    for raw in ("nan", "inf", "0.004"):
        value, error = validate_budget_amount(raw)
        assert value is None
        assert error is not None


def test_password_change_rules():
    errors = validate_password_change("", "newpass12", "newpass12")
    assert errors["current"] == "Enter your current password"

    errors = validate_password_change("old", "newpass12", "newpass99")
    assert errors["confirm"] == "The two passwords do not match"

    assert validate_password_change("old", "newpass12", "newpass12") == {}
