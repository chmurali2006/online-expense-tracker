"""CSV read and write for the import and export pages."""

import csv
import io

from app.services.validation import (
    PAYMENT_METHODS,
    validate_amount,
    validate_date,
    validate_note,
)

HEADER = ["date", "category", "amount", "payment_method", "note"]


def parse_csv(text, categories):
    """Returns (header_ok, rows, header_error).

    Each row is a dict with line_no, the five raw fields, an error string and a valid flag.
    Nothing is written to the database by this function.
    """
    if text is None:
        return False, [], "The file could not be read as text"

    try:
        decoded = text.lstrip("\ufeff")
        records = [r for r in csv.reader(io.StringIO(decoded)) if any(cell.strip() for cell in r)]
    except csv.Error:
        return False, [], "The file could not be read as CSV"

    if not records:
        return False, [], "The file is empty"

    header = [cell.strip().lower() for cell in records[0]]
    if header != HEADER:
        return False, [], "Header must be date,category,amount,payment_method,note"

    rows = []
    for index, record in enumerate(records[1:], start=2):
        fields = (record + ["", "", "", "", ""])[:5]
        raw = dict(zip(HEADER, [cell.strip() for cell in fields]))
        rows.append(check_row(index, raw, categories))
    return True, rows, None


def check_row(line_no, raw, categories):
    """One row, one error message. The first problem wins so the message stays short."""
    error = None

    _, date_error = validate_date(raw["date"])
    if date_error:
        error = "Bad date, use YYYY-MM-DD"

    amount, amount_error = validate_amount(raw["amount"])
    if error is None and amount_error:
        error = {
            "Amount is required": "Amount is required",
            "Amount must be more than 0": "Amount must be more than 0",
            "Amount is too large": "Amount is too large",
        }.get(amount_error, "Amount must be a number")

    _, note_error = validate_note(raw["note"])
    if error is None and note_error:
        error = note_error

    method = raw["payment_method"].lower()
    if error is None and method not in [m.lower() for m in PAYMENT_METHODS]:
        error = "Unknown payment method"
        method = None
    if method:
        method = next((m for m in PAYMENT_METHODS if m.lower() == method), method)

    category_id, category_error = validate_category_by_name(raw["category"], categories)
    if error is None and category_error:
        error = "Unknown category"

    return {
        "line_no": line_no,
        "date": raw["date"],
        "category": raw["category"],
        "amount": amount,
        "payment_method": method,
        "category_id": category_id,
        "note": raw["note"],
        "error": error,
        "valid": error is None,
    }


def validate_category_by_name(name, categories):
    # The import carries the category as text, the forms carry it as an id.
    wanted = (name or "").strip().lower()
    if not wanted:
        return None, "Choose a category"
    for category in categories:
        if category["name"].strip().lower() == wanted:
            return category["id"], None
    return None, "Unknown category"


def valid_rows(rows):
    return [row for row in rows if row["valid"]]


def csv_safe(value):
    """Neutralise spreadsheet formulas in cells written to a CSV export."""
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


def build_export(rows):
    out = io.StringIO()
    # Linux line endings, Excel and LibreOffice read them fine.
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(HEADER)
    for row in rows:
        writer.writerow([
            csv_safe(row["date"]),
            csv_safe(row["category_name"]),
            f"{row['amount']:.2f}",
            csv_safe(row["payment_method"]),
            csv_safe(row["note"]),
        ])
    return out.getvalue()
