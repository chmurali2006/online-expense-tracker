"""Month totals for the dashboard. Everything here is plain arithmetic."""

import calendar
from datetime import date

from app import queries
from app.services.budgets import budget_row


def shift_month(month, delta):
    """'2026-03' with -1 gives '2026-02'."""
    year, mon = int(month[:4]), int(month[5:7])
    mon += delta
    year += (mon - 1) // 12
    mon = (mon - 1) % 12 + 1
    return f"{year:04d}-{mon:02d}"


def valid_month(month):
    """True only for YYYY-MM strings that date() can actually represent."""
    if not (isinstance(month, str) and len(month) == 7 and month[4] == "-"
            and month[:4].isdigit() and month[5:].isdigit()):
        return False
    year, mon = int(month[:4]), int(month[5:7])
    return 1 <= year <= 9999 and 1 <= mon <= 12


def month_label(month):
    year, mon = int(month[:4]), int(month[5:7])
    return date(year, mon, 1).strftime("%B %Y")


def daily_series(user_id, month, totals):
    """One value per calendar day so the chart x axis is complete."""
    year, mon = int(month[:4]), int(month[5:7])
    days = calendar.monthrange(year, mon)[1]
    by_day = {row["day"]: row["total"] for row in totals}
    return [by_day.get(f"{d:02d}", 0) for d in range(1, days + 1)]


def comparison(total, previous_total):
    """Returns (difference in rupees, percent or None when there is no previous month)."""
    if previous_total is None:
        return None, None
    diff = round(float(total) - float(previous_total), 2)
    if previous_total == 0:
        return diff, None
    return diff, round(diff / float(previous_total) * 100.0, 2)


def build_month_summary(user_id, month):
    total = queries.month_total(user_id, month)
    previous_month = shift_month(month, -1)
    has_previous = queries.month_has_data(user_id, previous_month)
    # An empty previous month is still a comparison, but only if the user had
    # expenses before this month at all.
    first_month = queries.first_expense_month(user_id)
    if has_previous or (first_month and first_month < month):
        previous_total = queries.month_total(user_id, previous_month)
    else:
        previous_total = None
    diff, percent = comparison(total, previous_total)

    budget_rows = [budget_row(row) for row in queries.budgets_for_month(user_id, month)]
    daily = queries.month_daily_totals(user_id, month)

    return {
        "month": month,
        "label": month_label(month),
        "total": round(float(total), 2),
        "previous_total": previous_total,
        "difference": diff,
        "percent": percent,
        "categories": queries.month_category_totals(user_id, month),
        "daily": daily_series(user_id, month, daily),
        "has_data": queries.month_has_data(user_id, month),
        "recent": queries.recent_expenses(user_id, 5),
        "budget_rows": budget_rows,
        "budget_by_name": {row["category_name"]: row for row in budget_rows},
        "over_budget": [row for row in budget_rows if row["state"] == "over"],
    }
