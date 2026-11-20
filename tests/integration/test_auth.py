from app import queries


def test_TC_026_register_creates_account_and_default_categories(client, auth, app):
    response = auth.register("riya")
    assert response.status_code == 302
    assert response.headers["Location"].rstrip("/").endswith("/expenses")

    page = client.get("/expenses/")
    text = page.get_data(as_text=True)
    assert "Account created" in text
    assert "riya" in text

    with app.app_context():
        user = queries.get_user_by_username("riya")
        assert user is not None
        assert len(queries.list_categories(user["id"])) == 8
        assert "secret123" not in user["password_hash"]


def test_TC_027_duplicate_registration_is_refused(client, auth, app):
    auth.register("riya")
    auth.logout()
    response = auth.register("riya")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Username already taken" in text

    with app.app_context():
        assert queries.get_user_by_username("riya") is not None
        assert queries.get_user_by_username("riya.dupe") is None

    # The typed username stays in the form.
    assert 'value="riya"' in text


def test_TC_028_wrong_password_stays_on_the_login_page(client, auth):
    auth.register("riya")
    auth.logout()
    response = auth.login("riya", "notthe password")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Wrong username or password" in text

    ok = auth.login("riya", "secret123")
    assert ok.status_code == 302


def test_TC_029_logout_ends_the_session(client, auth):
    auth.register("riya")
    assert client.get("/expenses/").status_code == 200

    auth.logout()
    page = client.get("/expenses/")
    assert page.status_code == 302
    assert "/auth/login" in page.headers["Location"]


def test_TC_030_post_without_csrf_token_is_rejected(client, auth):
    auth.register("riya")
    response = client.post(
        "/expenses/",
        data={"amount": "120", "date": "2026-03-04", "category_id": "1", "payment_method": "cash", "note": ""},
    )
    assert response.status_code == 400
    assert "Bad request" in response.get_data(as_text=True)

    # A token that does not match the session is refused as well.
    response = client.post(
        "/expenses/",
        data={"amount": "120", "csrf_token": "deadbeef", "date": "2026-03-04", "category_id": "1", "payment_method": "cash"},
    )
    assert response.status_code == 400


def test_TC_031_change_password_checks_the_current_one(client, auth):
    auth.register("riya")

    response = auth.post("/auth/change-password", {"current": "wrongpass", "new": "newpass123", "confirm": "newpass123"})
    assert "Current password is wrong" in response.get_data(as_text=True)

    response = auth.post("/auth/change-password", {"current": "secret123", "new": "newpass123", "confirm": "newpass123"})
    assert response.status_code == 302

    auth.logout()
    assert auth.login("riya", "secret123").status_code == 200  # stays on page, wrong now
    assert auth.login("riya", "newpass123").status_code == 302


def test_login_requires_a_csrf_token(client, auth):
    auth.register("riya")
    auth.logout()
    response = client.post("/auth/login", data={"username": "riya", "password": "secret123"})
    assert response.status_code == 400


def test_backslash_redirect_target_is_not_accepted(client, auth):
    auth.register("riya")
    auth.logout()
    response = auth.login("riya", "secret123", path="/auth/login?next=/%5Cevil.example")
    assert response.status_code == 302
    assert response.headers["Location"] == "/expenses/"


def test_short_password_is_reported_inline(client, auth):
    response = auth.post("/auth/register", {"username": "ramu", "password": "short", "confirm": "short"})
    text = response.get_data(as_text=True)
    assert "Password needs at least 8 characters" in text
    assert 'id="password"' in text
