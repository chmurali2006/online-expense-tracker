from pathlib import Path

from app import queries


def test_layout_has_accessibility_and_mobile_hooks(client, auth):
    auth.register("riya")
    page = client.get("/expenses/").get_data(as_text=True)

    assert 'class="skip-link" href="#main-content"' in page
    assert 'id="main-content"' in page
    assert 'id="nav-toggle"' in page
    assert 'aria-current="page"' in page
    assert 'aria-live="polite"' in page
    assert "favicon.svg" in page
    assert 'class="filters-heading">Filters' in page
    assert client.get("/robots.txt").status_code == 200


def test_expense_table_has_mobile_card_hooks(client, auth, app):
    auth.register("riya")
    with app.app_context():
        uid = queries.get_user_by_username("riya")["id"]
        category = queries.list_categories(uid)[0]
        queries.insert_expense(uid, {
            "category_id": category["id"],
            "amount": 120.0,
            "date": "2026-03-04",
            "payment_method": "cash",
            "note": "Mobile layout check",
        })

    page = client.get("/expenses/").get_data(as_text=True)
    assert 'class="table-dense responsive-cards"' in page
    assert 'data-label="Amount"' in page
    assert 'data-label="Actions"' in page
    assert 'scope="col"' in page

    with app.app_context():
        uid = queries.get_user_by_username("riya")["id"]
        rows, _ = queries.list_expenses(uid, per_page=1)
        expense_id = rows[0]["id"]
    delete_page = client.get(f"/expenses/{expense_id}/delete").get_data(as_text=True)
    assert '<th scope="row" class="muted">Date</th>' in delete_page
    assert '<th scope="row" class="muted">Category</th>' in delete_page


def test_stylesheet_defines_responsive_breakpoints():
    css_path = Path(__file__).resolve().parents[2] / "app" / "static" / "css" / "app.css"
    css = css_path.read_text(encoding="utf-8")

    assert "@media (max-width: 1120px)" in css
    assert "@media (max-width: 1100px)" in css
    assert "@media (max-width: 800px)" in css
    assert "@media (max-width: 560px)" in css
    assert "@media print" in css
    assert "table.responsive-cards" in css
    assert "prefers-reduced-motion" in css
    assert "grid-template-columns: repeat(auto-fit, minmax(150px, 1fr))" in css
    assert "min-height: 40px" in css
    assert ".hint .mono" in css
    assert "clip-path: inset(50%)" in css
    assert ".card-head > a.eyebrow" in css
    assert ".pie-layout { flex-direction: column" in css
    assert 'td[data-label="Rename"]' in css
