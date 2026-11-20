import json
import re
from datetime import date
from pathlib import Path

from app import queries


def test_dashboard_has_category_pie_chart_data(client, auth, app):
    auth.register("riya")
    today = date.today()
    month = today.strftime("%Y-%m")
    with app.app_context():
        uid = queries.get_user_by_username("riya")["id"]
        categories = {c["name"]: c for c in queries.list_categories(uid)}
        for name, amount in (("Food", 120.0), ("Travel", 80.5)):
            queries.insert_expense(uid, {
                "category_id": categories[name]["id"],
                "amount": amount,
                "date": f"{month}-04",
                "payment_method": "cash",
                "note": f"{name} chart check",
            })

    page = client.get("/dashboard/").get_data(as_text=True)
    assert 'id="category-chart"' in page
    assert "Category split" in page

    match = re.search(r'<script id="dashboard-data"[^>]*>(.*?)</script>', page, re.S)
    assert match, "dashboard chart data is missing"
    payload = json.loads(match.group(1))
    assert set(payload["categoryLabels"]) == {"Food", "Travel"}
    assert round(sum(payload["categoryValues"]), 2) == 200.5
    assert len(payload["categoryColors"]) >= len(payload["categoryLabels"])


def test_every_visible_field_has_a_label_and_card_cells_have_data_labels(client, auth, app):
    auth.register("riya")
    with app.app_context():
        uid = queries.get_user_by_username("riya")["id"]
        category_id = queries.list_categories(uid)[0]["id"]

    paths = (
        "/expenses/",
        "/expenses/new",
        "/categories/",
        f"/categories/{category_id}/delete",
        "/budgets/",
        "/import",
        "/auth/change-password",
    )
    for path in paths:
        page = client.get(path).get_data(as_text=True)
        controls = re.findall(r"<(?:input|select|textarea)\b[^>]*>", page)
        ids = []
        for control in controls:
            if re.search(r'type="hidden"', control):
                continue
            found = re.search(r'\bid="([^"]+)"', control)
            assert found, f"visible control without id on {path}: {control}"
            ids.append(found.group(1))
        for control_id in ids:
            assert re.search(r'<label[^>]*\bfor="' + re.escape(control_id) + r'"', page), (
                f"no label for {control_id} on {path}"
            )

        tables = re.findall(r'<table class="table-dense responsive-cards">.*?</table>', page, re.S)
        for table in tables:
            cells = re.findall(r"<td\b[^>]*>", table)
            assert cells
            for cell in cells:
                assert "data-label=" in cell, f"card cell without data-label on {path}: {cell}"


def test_pie_chart_draws_labels_on_slices():
    js_path = Path(__file__).resolve().parents[2] / "app" / "static" / "js" / "dashboard.js"
    js = js_path.read_text(encoding="utf-8")

    assert 'id: "pieLabels"' in js
    assert "afterDatasetsDraw" in js
    assert "pieLabels: { enabled: true }" in js
    assert "strokeText" in js
    assert "fillText" in js
