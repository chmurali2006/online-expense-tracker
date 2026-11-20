import math
from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from app import queries
from app.services.validation import PAYMENT_METHODS, validate_date, validate_expense

bp = Blueprint("expenses", __name__)

PER_PAGE = 15
MAX_PAGE = 100000
MAX_ID = 9223372036854775807  # SQLite INTEGER range
FILTER_KEYS = ("date_from", "date_to", "category_id", "method", "q", "sort", "direction")


def read_filters(args):
    """Filters come from the query string. Anything that does not parse is dropped."""
    filters = {
        "date_from": "",
        "date_to": "",
        "category_id": "",
        "method": "",
        "q": (args.get("q") or "").strip()[:80],
        "sort": args.get("sort") if args.get("sort") in ("date", "amount") else "date",
        "direction": args.get("direction") if args.get("direction") in ("asc", "desc") else "desc",
    }
    for key in ("date_from", "date_to"):
        parsed, _ = validate_date(args.get(key))
        filters[key] = parsed or ""
    raw_category = args.get("category_id", "")
    if raw_category.isdigit() and len(raw_category) <= 19 and int(raw_category) <= MAX_ID:
        filters["category_id"] = str(int(raw_category))
    if args.get("method") in PAYMENT_METHODS:
        filters["method"] = args.get("method")
    return filters


def query_string(filters, **extra):
    from urllib.parse import urlencode

    params = [(k, v) for k, v in filters.items() if v]
    params += [(k, v) for k, v in extra.items() if v]
    return urlencode(params)


def page_count(total):
    return max(1, math.ceil(total / PER_PAGE)) if total else 1


def load_page(filters, page):
    rows, total = queries.list_expenses(
        g.user["id"],
        date_from=filters["date_from"] or None,
        date_to=filters["date_to"] or None,
        category_id=filters["category_id"] or None,
        method=filters["method"] or None,
        q=filters["q"] or None,
        sort=filters["sort"],
        direction=filters["direction"],
        page=page,
        per_page=PER_PAGE,
    )
    pages = page_count(total)
    if page > pages:
        page = pages
        rows, total = queries.list_expenses(
            g.user["id"],
            date_from=filters["date_from"] or None,
            date_to=filters["date_to"] or None,
            category_id=filters["category_id"] or None,
            method=filters["method"] or None,
            q=filters["q"] or None,
            sort=filters["sort"],
            direction=filters["direction"],
            page=page,
            per_page=PER_PAGE,
        )
    return rows, total, page, pages


@bp.route("/")
def index():
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))
    return redirect(url_for("dashboard.index"))


@bp.route("/expenses", methods=("GET", "POST"))
@bp.route("/expenses/", methods=("GET", "POST"))
def list():
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    categories = queries.list_categories(g.user["id"])
    filters = read_filters(request.args)

    if request.method == "POST":
        data, errors = validate_expense(request.form, categories)
        if errors:
            for message in errors.values():
                flash(message, "error")
            # Keep what was typed so a mistake does not mean retyping the row.
            session["quick_add"] = {
                key: request.form.get(key, "")
                for key in ("amount", "date", "category_id", "payment_method", "note")
            }
        else:
            queries.insert_expense(g.user["id"], data)
            session.pop("quick_add", None)
            flash("Expense added")
        return redirect("/expenses/" + (("?" + query_string(filters)) if query_string(filters) else ""))

    raw_page = str(request.args.get("page", "1"))
    page = int(raw_page) if raw_page.isdigit() and len(raw_page) <= 6 and 0 < int(raw_page) <= MAX_PAGE else 1
    rows, total, page, pages = load_page(filters, page)
    quick_add = session.pop("quick_add", {})

    return render_template(
        "expenses/list.html",
        rows=rows,
        total=total,
        page=page,
        pages=pages,
        filters=filters,
        categories=categories,
        qs=query_string(filters),
        query_before=query_string(filters, page=page - 1 if page > 1 else ""),
        query_next=query_string(filters, page=page + 1),
        today=date.today().isoformat(),
        quick_add=quick_add,
        empty_reason=bool(
            filters["date_from"] or filters["date_to"] or filters["category_id"] or filters["method"] or filters["q"]
        ),
    )


@bp.route("/expenses/new", methods=("GET", "POST"))
def new():
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    categories = queries.list_categories(g.user["id"])
    errors = {}
    form = {"amount": "", "date": date.today().isoformat(), "category_id": "", "payment_method": "cash", "note": ""}
    if request.method == "POST":
        form = {key: request.form.get(key, "") for key in form}
        data, errors = validate_expense(request.form, categories)
        if not errors:
            queries.insert_expense(g.user["id"], data)
            flash("Expense added")
            return redirect(url_for("expenses.list"))

    return render_template("expenses/new.html", errors=errors, form=form, categories=categories)


@bp.route("/expenses/<int:expense_id>/edit", methods=("GET", "POST"))
def edit(expense_id):
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    expense = queries.get_expense(g.user["id"], expense_id)
    if expense is None:
        return render_template("errors/404.html"), 404

    categories = queries.list_categories(g.user["id"])
    errors = {}
    if request.method == "POST":
        data, errors = validate_expense(request.form, categories)
        if not errors:
            queries.update_expense(g.user["id"], expense_id, data)
            flash("Expense updated")
            return redirect(url_for("expenses.list"))
        # Show the values that were actually submitted, not the stored row,
        # so an invalid field can be corrected without retyping the rest.
        expense = {
            **expense,
            **{
                key: request.form.get(key, "")
                for key in ("amount", "date", "category_id", "payment_method", "note")
            },
        }

    return render_template("expenses/edit.html", expense=expense, errors=errors, categories=categories)


@bp.route("/expenses/<int:expense_id>/delete", methods=("GET", "POST"))
def delete(expense_id):
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    expense = queries.get_expense(g.user["id"], expense_id)
    if expense is None:
        return render_template("errors/404.html"), 404

    if request.method == "POST":
        queries.delete_expense(g.user["id"], expense_id)
        flash("Expense deleted")
        return redirect(url_for("expenses.list"))

    return render_template("expenses/delete.html", expense=expense)
