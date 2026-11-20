from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app import queries
from app.services.budgets import budget_row
from app.services.summary import month_label, shift_month, valid_month
from app.services.validation import validate_budget_amount

bp = Blueprint("budgets", __name__, url_prefix="/budgets")


def wanted_month():
    from datetime import date

    today = date.today().strftime("%Y-%m")
    month = request.args.get("month") or request.form.get("month") or ""
    if not valid_month(month) or month > today:
        return today
    return month


@bp.route("/", methods=("GET", "POST"))
def index():
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    month = wanted_month()
    categories = queries.list_categories(g.user["id"])

    if request.method == "POST":
        amount, error = validate_budget_amount(request.form.get("amount"))
        try:
            category_id = int(request.form.get("category_id"))
        except (TypeError, ValueError):
            category_id = 0
        if not error and not queries.get_category(g.user["id"], category_id):
            error = "Choose a category"
        if error:
            flash(error, "error")
        else:
            queries.set_budget(g.user["id"], category_id, month, amount)
            flash("Budget saved")
        return redirect(url_for("budgets.index", month=month))

    rows = [budget_row(row) for row in queries.budgets_for_month(g.user["id"], month)]
    return render_template(
        "budgets/index.html",
        rows=rows,
        month=month,
        label=month_label(month),
        categories=categories,
        has_budget={row["category_id"] for row in rows},
        prev_month=shift_month(month, -1),
        next_month=shift_month(month, 1),
    )
