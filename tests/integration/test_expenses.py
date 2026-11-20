from app import queries


def add(auth, amount="150", date="2026-03-04", category="1", method="cash", note="note", path="/expenses/"):
    return auth.post(
        path,
        {
            "amount": amount,
            "date": date,
            "category_id": category,
            "payment_method": method,
            "note": note,
        },
        follow_redirects=True,
    )


def count(app, user_id):
    with app.app_context():
        rows, total = queries.list_expenses(user_id, per_page=0)
        return total


def user_id_of(app):
    with app.app_context():
        return queries.get_user_by_username("riya")["id"]


def test_TC_032_add_expense_with_valid_data(client, auth, app):
    auth.register("riya")
    response = add(auth, amount="250", note="Auto fare to college", method="UPI")
    text = response.get_data(as_text=True)
    assert "Expense added" in text
    assert "Auto fare to college" in text
    assert "250.00" in text
    assert count(app, user_id_of(app)) == 1


def test_TC_033_add_with_amount_zero_shows_an_error_and_writes_nothing(client, auth, app):
    auth.register("riya")
    response = add(auth, amount="0", note="Should not save")
    text = response.get_data(as_text=True)
    assert "Amount must be more than 0" in text
    assert count(app, user_id_of(app)) == 0
    assert "<td>Should not save</td>" not in text  # nothing was stored as a row

    # The rest of what was typed is kept in the form.
    assert 'value="Should not save"' in text
    assert 'placeholder="Auto fare to college"' in text


def test_TC_034_edit_an_expense(client, auth, app):
    auth.register("riya")
    add(auth, amount="120", note="Chai")
    uid = user_id_of(app)
    with app.app_context():
        expense = queries.list_expenses(uid, per_page=0)[0][0]

    response = auth.post(
        f"/expenses/{expense['id']}/edit",
        {"amount": "150", "date": "2026-03-04", "category_id": "2", "payment_method": "card", "note": "Chai and biscuits"},
        follow_redirects=True,
    )
    text = response.get_data(as_text=True)
    assert "Expense updated" in text
    assert "150.00" in text
    assert "Chai and biscuits" in text

    bad = auth.post(
        f"/expenses/{expense['id']}/edit",
        {"amount": "", "date": "2026-03-04", "category_id": "2", "payment_method": "card", "note": "x"},
    )
    assert "Amount is required" in bad.get_data(as_text=True)


def test_TC_035_delete_needs_a_confirm_step(client, auth, app):
    auth.register("riya")
    add(auth, amount="90", note="Delete me")
    uid = user_id_of(app)
    with app.app_context():
        expense = queries.list_expenses(uid, per_page=0)[0][0]

    confirm = client.get(f"/expenses/{expense['id']}/delete")
    assert confirm.status_code == 200
    assert "Delete this expense?" in confirm.get_data(as_text=True)
    assert count(app, uid) == 1  # opening the page removes nothing

    back = client.get("/expenses/")
    assert back.status_code == 200

    done = auth.post(f"/expenses/{expense['id']}/delete", {}, follow_redirects=True)
    assert "Expense deleted" in done.get_data(as_text=True)
    assert count(app, uid) == 0


def test_TC_036_cannot_open_another_users_expense(client, auth, app):
    auth.register("riya")
    add(auth, amount="1200", note="Riya private")
    uid = user_id_of(app)
    with app.app_context():
        expense = queries.list_expenses(uid, per_page=0)[0][0]
    auth.logout()

    auth.register("sam", password="another12")
    assert client.get(f"/expenses/{expense['id']}/edit").status_code == 404
    assert client.get(f"/expenses/{expense['id']}/delete").status_code == 404

    page = auth.post(
        f"/expenses/{expense['id']}/delete", {}, follow_redirects=True
    )
    assert page.status_code == 404

    with app.app_context():
        assert queries.get_expense(uid, expense["id"]) is not None


def test_TC_037_filters_by_date_range_category_and_method(client, auth, app):
    auth.register("riya")
    add(auth, amount="100", date="2026-03-04", category="1", method="UPI", note="March food")
    add(auth, amount="200", date="2026-03-20", category="2", method="cash", note="March travel")
    add(auth, amount="300", date="2026-04-05", category="1", method="card", note="April food")

    page = client.get("/expenses/?date_from=2026-03-01&date_to=2026-03-31").get_data(as_text=True)
    assert "2 rows" in page
    assert "March food" in page and "March travel" in page
    assert "April food" not in page

    page = client.get("/expenses/?category_id=1").get_data(as_text=True)
    assert "2 rows" in page
    assert "April food" in page and "March travel" not in page

    page = client.get("/expenses/?method=UPI").get_data(as_text=True)
    assert "1 row" in page and "March food" in page

    page = client.get("/expenses/?date_from=2027-01-01").get_data(as_text=True)
    assert "No expenses match these filters" in page


def test_TC_038_search_inside_the_note_and_sort_by_amount(client, auth, app):
    auth.register("riya")
    add(auth, amount="150", note="Auto fare to college")
    add(auth, amount="900", note="Reference book")
    add(auth, amount="75", note="Canteen lunch")

    page = client.get("/expenses/?q=fare").get_data(as_text=True)
    assert "1 row" in page
    assert "Auto fare to college" in page
    assert "Reference book" not in page

    page = client.get("/expenses/?sort=amount&direction=desc").get_data(as_text=True)
    amounts = [line for line in page.split("num\">")[1:]]
    assert "900.00" in page
    assert page.index("900.00") < page.index("75.00")

    page = client.get("/expenses/?sort=amount&direction=asc&q=canteen").get_data(as_text=True)
    assert "Canteen lunch" in page


def test_TC_039_pagination_boundaries(client, auth, app):
    from datetime import date, timedelta

    auth.register("riya")
    uid = user_id_of(app)
    today = date(2026, 3, 31)
    with app.app_context():
        categories = queries.list_categories(uid)
        for index in range(31):
            queries.insert_expense(
                uid,
                {
                    "category_id": categories[0]["id"],
                    "amount": float(index + 1),
                    "date": (today - timedelta(days=index)).isoformat(),
                    "payment_method": "cash",
                    "note": f"row {index + 1}",
                },
            )

    first = client.get("/expenses/").get_data(as_text=True)
    assert "Page 1 of 3" in first
    assert first.count("row ") == 15
    assert "31 rows" in first

    second = client.get("/expenses/?page=2").get_data(as_text=True)
    assert "Page 2 of 3" in second

    last = client.get("/expenses/?page=3").get_data(as_text=True)
    assert "Page 3 of 3" in last
    assert "Next" in last

    zero = client.get("/expenses/?page=0")
    assert zero.status_code == 200
    assert "Page 1 of 3" in zero.get_data(as_text=True)

    beyond = client.get("/expenses/?page=99").get_data(as_text=True)
    assert "Page 3 of 3" in beyond
    assert "No expenses match these filters" not in beyond

    # A page number that is not a number falls back to the first page.
    broken = client.get("/expenses/?page=abc")
    assert broken.status_code == 200
    assert "Page 1 of 3" in broken.get_data(as_text=True)


def test_TC_040_quick_add_keeps_the_current_filters(client, auth, app):
    auth.register("riya")
    add(auth, amount="100", date="2026-03-04", method="UPI", note="first")

    target = "/expenses/?method=UPI&sort=amount&direction=asc"
    response = client.post(
        target,
        data={
            "amount": "60",
            "date": "2026-03-04",
            "category_id": "1",
            "payment_method": "UPI",
            "note": "quick one",
            "csrf_token": auth.token("/expenses/?method=UPI"),
        },
        follow_redirects=True,
    )
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Expense added" in text
    assert "quick one" in text
    assert "method=UPI" in text

    with app.app_context():
        rows, total = queries.list_expenses(user_id_of(app), method="UPI", per_page=0)
        assert total == 2
        assert rows[0]["amount"] == 60.0  # sort by amount ascending kept


def test_login_required_for_the_list_page(client):
    page = client.get("/expenses/")
    assert page.status_code == 302
    assert "/auth/login" in page.headers["Location"]


def test_oversized_query_parameters_do_not_break_the_page(client, auth):
    auth.register("riya")
    huge = "9" * 100
    for path in (
        f"/expenses/?page={huge}",
        f"/expenses/?category_id={huge}",
        "/expenses/?page=999999999999999999999",
        "/expenses/?category_id=999999999999999999999",
    ):
        response = client.get(path)
        assert response.status_code == 200
        assert "Expenses" in response.get_data(as_text=True)


def test_edit_page_shows_when_the_expense_was_added(client, auth, app):
    auth.register("riya")
    add(auth, amount="120", note="Chai")
    uid = user_id_of(app)
    with app.app_context():
        expense = queries.list_expenses(uid, per_page=0)[0][0]

    page = client.get(f"/expenses/{expense['id']}/edit").get_data(as_text=True)
    assert "added on" in page
    assert expense["created_at"] in page
    assert "added on ." not in page


def test_edit_keeps_typed_values_when_one_field_is_invalid(client, auth, app):
    auth.register("riya")
    add(auth, amount="120", note="Chai")
    uid = user_id_of(app)
    with app.app_context():
        expense = queries.list_expenses(uid, per_page=0)[0][0]

    bad = auth.post(
        f"/expenses/{expense['id']}/edit",
        {
            "amount": "150",
            "date": "not-a-date",
            "category_id": "2",
            "payment_method": "card",
            "note": "Chai and biscuits",
        },
    )
    text = bad.get_data(as_text=True)
    assert "Use the date format YYYY-MM-DD" in text
    assert 'value="150"' in text
    assert 'value="not-a-date"' in text
    assert 'value="Chai and biscuits"' in text


def test_quick_add_form_posts_like_a_real_browser(client, auth, app):
    """The quick-add form must carry its own CSRF field: a browser cannot inject one."""
    import re

    auth.register("riya")
    page = client.get("/expenses/").get_data(as_text=True)
    quick_add = page.split('<form class="quick-add"', 1)[1].split("</form>", 1)[0]
    token = re.search(r'name="csrf_token" value="([0-9a-f]+)"', quick_add).group(1)

    response = client.post(
        "/expenses/",
        data={
            "amount": "80",
            "date": "2026-03-04",
            "category_id": "1",
            "payment_method": "cash",
            "note": "From the rendered form",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Expense added" in response.get_data(as_text=True)
    assert count(app, user_id_of(app)) == 1
