import json
import secrets
from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, request, send_file, session, url_for

from app import queries
from app.routes.expenses import query_string, read_filters
from app.services.csv_io import HEADER, build_export, parse_csv, valid_rows

bp = Blueprint("data", __name__)


def staged_batch():
    token = session.get("import_token")
    return queries.get_import_batch(token) if token else None


def staged_rows():
    batch = staged_batch()
    return json.loads(batch["rows_json"]) if batch else None


def staged_filename():
    batch = staged_batch()
    return batch["filename"] if batch else None


@bp.route("/expenses/export")
def export():
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    filters = read_filters(request.args)
    rows, _ = queries.list_expenses(
        g.user["id"],
        date_from=filters["date_from"] or None,
        date_to=filters["date_to"] or None,
        category_id=filters["category_id"] or None,
        method=filters["method"] or None,
        q=filters["q"] or None,
        sort=filters["sort"],
        direction=filters["direction"],
        per_page=0,
    )
    import io

    payload = build_export(rows)
    name = f"expenses-{date.today().isoformat()}.csv"
    return send_file(
        io.BytesIO(payload.encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=name,
    )


@bp.route("/import", methods=("GET", "POST"))
def upload():
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    if request.method == "POST":
        stored = request.files.get("file")
        if stored is None or not stored.filename:
            flash("Choose a CSV file first", "error")
            return redirect(url_for("data.upload"))

        if not stored.filename.lower().endswith(".csv"):
            flash("The file must be a .csv", "error")
            return redirect(url_for("data.upload"))

        try:
            text = stored.read().decode("utf-8-sig", errors="replace")
        except Exception:
            flash("The file could not be read as text", "error")
            return redirect(url_for("data.upload"))

        categories = queries.list_categories(g.user["id"])
        header_ok, rows, header_error = parse_csv(text, categories)
        if not header_ok:
            flash(header_error, "error")
            return redirect(url_for("data.upload"))

        # Only a small token goes into the cookie; the rows stay on the server.
        token = secrets.token_urlsafe(16)
        queries.create_import_batch(token, stored.filename, json.dumps(rows))
        session["import_token"] = token
        return redirect(url_for("data.preview"))

    return render_template(
        "data/import.html", rows=staged_rows(), filename=staged_filename(), header=HEADER
    )


@bp.route("/import/preview", methods=("GET", "POST"))
def preview():
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    batch = staged_batch()
    rows = json.loads(batch["rows_json"]) if batch else None
    if not rows:
        flash("Upload a file first", "error")
        return redirect(url_for("data.upload"))

    if request.method == "POST":
        action = request.form.get("action")
        if action == "cancel":
            queries.delete_import_batch(session["import_token"])
            session.pop("import_token", None)
            flash("Import cancelled")
            return redirect(url_for("data.upload"))
        if action != "import":
            flash("Choose import or cancel", "error")
            return redirect(url_for("data.preview"))

        good = valid_rows(rows)
        # One transaction: a failure part-way through leaves nothing behind.
        queries.insert_expenses(g.user["id"], good)
        queries.delete_import_batch(session["import_token"])
        session.pop("import_token", None)
        skipped = len(rows) - len(good)
        flash(f"{len(good)} added, {skipped} skipped")
        return redirect(url_for("expenses.list"))

    return render_template(
        "data/preview.html", rows=rows, filename=batch["filename"], header=HEADER
    )
