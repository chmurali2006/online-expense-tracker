from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from app import queries
from app.services.validation import validate_category_name

bp = Blueprint("categories", __name__, url_prefix="/categories")


@bp.route("/", methods=("GET", "POST"))
def index():
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    errors = {}
    if request.method == "POST":
        name, errors = validate_category_name(
            request.form.get("name"), [c["name"] for c in queries.list_categories(g.user["id"])]
        )
        if not errors:
            queries.insert_category(g.user["id"], name)
            flash("Category added")
            return redirect(url_for("categories.index"))

    return render_template(
        "categories/index.html",
        rows=queries.categories_with_counts(g.user["id"]),
        errors=errors,
        form_name=request.form.get("name", "") if request.method == "POST" else "",
    )


@bp.post("/<int:category_id>/rename")
def rename(category_id):
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    category = queries.get_category(g.user["id"], category_id)
    if category is None:
        return render_template("errors/404.html"), 404

    others = [c["name"] for c in queries.list_categories(g.user["id"]) if c["id"] != category_id]
    name, error = validate_category_name(request.form.get("name"), others)
    if error:
        flash(error, "error")
    else:
        queries.rename_category(g.user["id"], category_id, name)
        flash("Category renamed")
    return redirect(url_for("categories.index"))


@bp.route("/<int:category_id>/delete", methods=("GET", "POST"))
def delete(category_id):
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    category = queries.get_category(g.user["id"], category_id)
    if category is None:
        return render_template("errors/404.html"), 404

    count = queries.count_category_expenses(category_id, g.user["id"])
    others = [c for c in queries.list_categories(g.user["id"]) if c["id"] != category_id]

    if request.method == "POST":
        if count:
            target_id = request.form.get("move_to", "")
            target = next((c for c in others if str(c["id"]) == target_id), None)
            if target is None:
                flash("Choose the category that takes these expenses", "error")
                return render_template(
                    "categories/delete.html", category=category, count=count, others=others, error=True
                )
            queries.move_category_expenses(category_id, target["id"], g.user["id"])
            queries.delete_category(g.user["id"], category_id)
            flash(f"Expenses moved to {target['name']}")
            return redirect(url_for("categories.index"))
        queries.delete_category(g.user["id"], category_id)
        flash("Category deleted")
        return redirect(url_for("categories.index"))

    if count:
        return render_template("categories/delete.html", category=category, count=count, others=others, error=False)

    return render_template("categories/confirm.html", category=category)
