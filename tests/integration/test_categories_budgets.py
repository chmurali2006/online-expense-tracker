from app import queries


def add(auth, amount="150", date="2026-03-04", category="1", method="cash", note="note"):
    return auth.post(
        "/expenses/",
        {"amount": amount, "date": date, "category_id": category, "payment_method": method, "note": note},
    )


def user_id_of(app):
    with app.app_context():
        return queries.get_user_by_username("riya")["id"]


def test_TC_041_category_in_use_asks_where_the_expenses_go(client, auth, app):
    auth.register("riya")
    uid = user_id_of(app)
    for index in range(3):
        add(auth, amount=str(100 + index), category="1", note=f"food {index}")

    with app.app_context():
        food = queries.get_category_by_name(uid, "Food")
        travel = queries.get_category_by_name(uid, "Travel")

    page = client.get(f"/categories/{food['id']}/delete")
    text = page.get_data(as_text=True)
    assert page.status_code == 200
    assert "This category is in use" in text
    assert ">3<" in text.replace(" ", "")
    assert "Travel" in text

    # Confirming without choosing a target does nothing.
    refused = auth.post(f"/categories/{food['id']}/delete", {"move_to": ""})
    assert "Choose the category that takes these expenses" in refused.get_data(as_text=True)
    with app.app_context():
        assert queries.count_category_expenses(food["id"], uid) == 3

    moved = auth.post(f"/categories/{food['id']}/delete", {"move_to": str(travel["id"])}, follow_redirects=True)
    assert "Expenses moved to Travel" in moved.get_data(as_text=True)
    with app.app_context():
        assert queries.get_category(uid, food["id"]) is None
        assert queries.count_category_expenses(travel["id"], uid) == 3
        assert queries.count_category_expenses(food["id"], uid) == 0


def test_TC_042_rename_a_category_and_add_a_new_one(client, auth, app):
    auth.register("riya")
    uid = user_id_of(app)
    add(auth, note="chandan")

    with app.app_context():
        food = queries.get_category_by_name(uid, "Food")

    page = auth.post(f"/categories/{food['id']}/rename", {"name": "Meals"}, follow_redirects=True)
    assert "Category renamed" in page.get_data(as_text=True)
    with app.app_context():
        assert queries.get_category(uid, food["id"])["name"] == "Meals"

    duplicate = auth.post(f"/categories/{food['id']}/rename", {"name": "travel"}, follow_redirects=True)
    assert "You already have a category with this name" in duplicate.get_data(as_text=True)

    created = auth.post("/categories/", {"name": "Metro card"}, follow_redirects=True)
    assert "Category added" in created.get_data(as_text=True)
    with app.app_context():
        assert queries.get_category_by_name(uid, "Metro card") is not None

    # The renamed category shows on the expense rows.
    assert "Meals" in client.get("/expenses/").get_data(as_text=True)


def test_TC_043_budget_bar_changes_colour_at_80_and_100_percent(client, auth, app):
    auth.register("riya")
    uid = user_id_of(app)
    with app.app_context():
        food = queries.get_category_by_name(uid, "Food")

    auth.post("/budgets/", {"month": "2026-03", "category_id": str(food["id"]), "amount": "1000"})
    add(auth, amount="799", date="2026-03-04", category=str(food["id"]), note="under")

    page = client.get("/budgets/?month=2026-03").get_data(as_text=True)
    assert "79.9%" in page
    assert 'class="bar ok"' in page
    assert "under budget" in page

    add(auth, amount="1", date="2026-03-05", category=str(food["id"]), note="to eighty")
    page = client.get("/budgets/?month=2026-03").get_data(as_text=True)
    assert "80.0%" in page
    assert 'class="bar warn"' in page
    assert "nearly there" in page

    add(auth, amount="200", date="2026-03-06", category=str(food["id"]), note="over the top")
    page = client.get("/budgets/?month=2026-03").get_data(as_text=True)
    assert "100.0%" in page
    assert 'class="bar over"' in page
    assert "over budget" in page

    page = auth.post(
        "/budgets/",
        {"month": "2026-03", "category_id": str(food["id"]), "amount": "-5"},
        follow_redirects=True,
    )
    assert "Budget must be more than 0" in page.get_data(as_text=True)


def test_TC_044_dashboard_shows_the_total_and_the_difference(client, auth, app):
    auth.register("riya")
    uid = user_id_of(app)
    from datetime import date, timedelta

    from app.services.summary import shift_month

    today = date.today()
    this_month = today.strftime("%Y-%m")
    last_month = shift_month(this_month, -1)
    with app.app_context():
        food = queries.get_category_by_name(uid, "Food")
        queries.insert_expense(
            uid,
            {"category_id": food["id"], "amount": 18400.0, "date": f"{this_month}-04", "payment_method": "UPI", "note": "Mess bill"},
        )
        queries.insert_expense(
            uid,
            {"category_id": food["id"], "amount": 15000.0, "date": f"{last_month}-10", "payment_method": "cash", "note": "Old mess bill"},
        )
        queries.set_budget(uid, food["id"], this_month, 16000.0)

    page = client.get(f"/dashboard/?month={this_month}").get_data(as_text=True)
    assert "18,400.00" in page
    assert "+3,400.00" in page
    assert "+22.67%" in page
    assert "against last month" in page
    assert "Over budget" in page
    assert "Mess bill" in page
    assert "vendor/chart.umd.js" in page

    # Moving into the future is refused.
    page = client.get("/dashboard/?month=2099-01").get_data(as_text=True)
    assert "There is no future month yet" in page
    assert this_month in page


def test_malformed_month_falls_back_to_the_current_month(client, auth):
    auth.register("riya")
    for path in (
        "/dashboard/?month=2026-00",
        "/dashboard/?month=0000-01",
        "/dashboard/?month=2026-1%2F",
        "/budgets/?month=2026-00",
        "/budgets/?month=0000-01",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert "Something went wrong" not in response.get_data(as_text=True)


def test_TC_045_unknown_url_shows_the_404_page(client):
    response = client.get("/this/does/not/exist")
    assert response.status_code == 404
    text = response.get_data(as_text=True)
    assert "Page not found" in text
    assert "Back to the expense list" in text


def test_TC_046_empty_list_shows_one_sentence(client, auth):
    auth.register("riya")
    text = client.get("/expenses/").get_data(as_text=True)
    assert "Nothing here yet. Add your first expense above." in text
    assert "<tbody>" not in text


def test_TC_047_server_error_renders_the_500_page(client, auth, app, monkeypatch):
    auth.register("riya")

    from app.routes import expenses as expenses_module

    def boom(*args, **kwargs):
        raise RuntimeError("database gone")

    monkeypatch.setattr(expenses_module.queries, "list_expenses", boom)
    # TESTING normally re-raises, we want the real 500 page here.
    app.config["PROPAGATE_EXCEPTIONS"] = False
    response = client.get("/expenses/")
    assert response.status_code == 500
    assert "Something went wrong" in response.get_data(as_text=True)
