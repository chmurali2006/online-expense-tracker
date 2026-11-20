from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app import queries
from app.services.summary import build_month_summary, month_label, shift_month, valid_month

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def wanted_month(month_arg):
    # The switcher cannot move into the future.
    today = date.today().strftime("%Y-%m")
    if month_arg and valid_month(month_arg):
        if month_arg <= today:
            return month_arg
        flash("There is no future month yet", "error")
    return today


@bp.route("/")
def index():
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    month = wanted_month(request.args.get("month"))
    summary = build_month_summary(g.user["id"], month)
    first = queries.first_expense_month(g.user["id"])

    return render_template(
        "dashboard/index.html",
        summary=summary,
        month=month,
        label=summary["label"],
        prev_month=shift_month(month, -1),
        next_month=min(shift_month(month, 1), date.today().strftime("%Y-%m")),
        first_month=first,
        chart_labels=list(range(1, len(summary["daily"]) + 1)),
        chart_values=summary["daily"],
        chart_month=month_label(month),
        chart_category_labels=[row["name"] for row in summary["categories"]],
        chart_category_values=[round(float(row["total"]), 2) for row in summary["categories"]],
        chart_category_colors=[
            "#2F5D50", "#A64B2A", "#B8851F", "#6B7F94",
            "#7A6A53", "#4F7A6A", "#9A5B6B", "#5F6B45",
        ],
    )
