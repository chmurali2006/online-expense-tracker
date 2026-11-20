import io

from app import queries


def add(auth, amount="150", date="2026-03-04", category="1", method="cash", note="note"):
    return auth.post(
        "/expenses/",
        {"amount": amount, "date": date, "category_id": category, "payment_method": method, "note": note},
    )


def user_id_of(app):
    with app.app_context():
        return queries.get_user_by_username("riya")["id"]


def upload(auth, text, name="rows.csv"):
    return auth.post(
        "/import",
        {"file": (io.BytesIO(text.encode("utf-8")), name)},
        content_type="multipart/form-data",
        follow_redirects=True,
    )


def test_TC_048_export_only_contains_the_filtered_rows(client, auth, app):
    auth.register("riya")
    add(auth, amount="100", date="2026-03-04", method="UPI", note="Canteen lunch")
    add(auth, amount="200", date="2026-03-04", method="cash", note="Auto fare")
    add(auth, amount="300", date="2026-04-04", method="cash", note="April bus pass")

    response = client.get("/expenses/export?method=cash&date_from=2026-03-01&date_to=2026-03-31")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert "attachment" in response.headers["Content-Disposition"]

    lines = response.get_data(as_text=True).strip().split("\n")
    assert lines[0] == "date,category,amount,payment_method,note"
    assert len(lines) == 2
    assert "Auto fare" in lines[1]
    assert "Canteen lunch" not in response.get_data(as_text=True)
    assert "April bus pass" not in response.get_data(as_text=True)

    everything = client.get("/expenses/export").get_data(as_text=True)
    assert everything.count("\n") == 4


def test_TC_049_import_preview_then_confirm_inserts_only_valid_rows(client, auth, app):
    auth.register("riya")
    uid = user_id_of(app)

    text = (
        "date,category,amount,payment_method,note\n"
        "2026-03-04,Food,180.00,UPI,Canteen lunch\n"
        "31-02-2026,Food,90.00,cash,Broken date\n"
        "2026-03-05,Food,-5.00,cash,Negative amount\n"
        "2026-03-06,Magic,60.00,cash,Unknown category\n"
        "2026-03-07,Travel,45.00,cash,Auto fare to college\n"
    )
    page = upload(auth, text)
    body = page.get_data(as_text=True)
    assert "Check the file" in body
    assert "5 rows read" in body
    assert "2 valid" in body
    assert "3 with problems" in body
    assert "Bad date, use YYYY-MM-DD" in body
    assert "Amount must be more than 0" in body
    assert "Unknown category" in body
    assert "Import 2 valid rows" in body

    # Preview alone writes nothing.
    with app.app_context():
        assert queries.list_expenses(uid, per_page=0)[1] == 0

    done = auth.post("/import/preview", {"action": "import"}, token_path="/import", follow_redirects=True)
    assert "2 added, 3 skipped" in done.get_data(as_text=True)

    with app.app_context():
        rows, total = queries.list_expenses(uid, per_page=0)
        assert total == 2
        notes = sorted(row["note"] for row in rows)
        assert notes == ["Auto fare to college", "Canteen lunch"]
        assert all(row["amount"] > 0 for row in rows)


def test_TC_050_empty_csv_shows_an_error_and_adds_nothing(client, auth, app):
    auth.register("riya")
    uid = user_id_of(app)

    page = upload(auth, "")
    body = page.get_data(as_text=True)
    assert "The file is empty" in body
    with app.app_context():
        assert queries.list_expenses(uid, per_page=0)[1] == 0

    wrong = upload(auth, "Day;Cat;Amt\n2026-03-04;Food;10\n")
    assert "Header must be date,category,amount,payment_method,note" in wrong.get_data(as_text=True)

    missing = auth.post("/import", {}, content_type="multipart/form-data", follow_redirects=True)
    assert "Choose a CSV file first" in missing.get_data(as_text=True)

    not_csv = upload(auth, "date,category,amount,payment_method,note\n", name="rows.txt")
    assert "The file must be a .csv" in not_csv.get_data(as_text=True)


def test_TC_051_import_can_be_cancelled(client, auth, app):
    auth.register("riya")
    uid = user_id_of(app)
    text = "date,category,amount,payment_method,note\n2026-03-04,Food,180.00,UPI,Canteen lunch\n"

    upload(auth, text)
    cancelled = auth.post("/import/preview", {"action": "cancel"}, token_path="/import", follow_redirects=True)
    assert "Import cancelled" in cancelled.get_data(as_text=True)

    with app.app_context():
        assert queries.list_expenses(uid, per_page=0)[1] == 0

    # The preview is gone, so a direct confirm does not insert anything.
    upload(auth, text)
    auth.post("/import/preview", {"action": "cancel"}, token_path="/import")
    again = auth.post("/import/preview", {"action": "import"}, token_path="/import", follow_redirects=True)
    assert "Upload a file first" in again.get_data(as_text=True)
    with app.app_context():
        assert queries.list_expenses(uid, per_page=0)[1] == 0


def test_import_needs_an_explicit_action(client, auth, app):
    auth.register("riya")
    upload(auth, "date,category,amount,payment_method,note\n2026-03-04,Food,180.00,UPI,Canteen lunch\n")

    response = auth.post("/import/preview", {}, token_path="/import", follow_redirects=True)
    assert "Choose import or cancel" in response.get_data(as_text=True)
    with app.app_context():
        assert queries.list_expenses(user_id_of(app), per_page=0)[1] == 0


def test_large_import_is_staged_on_the_server_not_in_the_cookie(client, auth, app):
    auth.register("riya")
    lines = ["date,category,amount,payment_method,note"]
    for index in range(120):
        lines.append(
            f"2026-03-04,Food,10.00,UPI,Note number {index} with a long enough description to overflow a cookie"
        )

    page = upload(auth, "\n".join(lines) + "\n")
    text = page.get_data(as_text=True)
    assert "120 rows read" in text
    assert "120 valid" in text

    done = auth.post("/import/preview", {"action": "import"}, token_path="/import", follow_redirects=True)
    assert "120 added, 0 skipped" in done.get_data(as_text=True)
    with app.app_context():
        assert queries.list_expenses(user_id_of(app), per_page=0)[1] == 120


def test_failed_import_leaves_no_partial_rows(client, auth, app, monkeypatch):
    import pytest

    auth.register("riya")
    upload(auth, "date,category,amount,payment_method,note\n2026-03-04,Food,180.00,UPI,Canteen lunch\n")

    from app.routes import data as data_module

    def boom(*args, **kwargs):
        raise RuntimeError("disk gone")

    monkeypatch.setattr(data_module.queries, "insert_expenses", boom)
    with pytest.raises(RuntimeError):
        auth.post("/import/preview", {"action": "import"}, token_path="/import")

    with app.app_context():
        assert queries.list_expenses(user_id_of(app), per_page=0)[1] == 0
    # The batch is still staged, so the user can retry the import.
    assert "1 row read" in client.get("/import/preview").get_data(as_text=True)


def test_export_requires_login(client):
    response = client.get("/expenses/export")
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_seed_script_creates_demo_data(app):
    from app.seed import seed_demo_user

    with app.app_context():
        created, message = seed_demo_user()
        assert created
        demo = queries.get_user_by_username("demo")
        assert len(queries.list_categories(demo["id"])) == 8
        _, total = queries.list_expenses(demo["id"], per_page=0)
        assert 45 <= total <= 60
        again, _ = seed_demo_user()
        assert not again  # running it twice does not double the data
    assert "demo user" in message
