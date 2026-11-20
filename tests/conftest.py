import re

import pytest

from app import create_app


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "DATABASE": str(tmp_path / "test.sqlite3"),
            "TESTING": True,
            "SECRET_KEY": "test-secret",
        }
    )
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


class Auth:
    """Login helpers. The CSRF token has to be fetched from a real page, like a browser would."""

    def __init__(self, client):
        self.client = client

    def token(self, path="/expenses/"):
        # Some endpoints only exist as POST, so fall back to a page that has a form.
        for candidate in (path, "/expenses/", "/categories/"):
            page = self.client.get(candidate)
            match = re.search(r'name="csrf_token" value="([0-9a-f]+)"', page.get_data(as_text=True))
            if match:
                return match.group(1)
        raise AssertionError(f"no csrf token on {path}")

    def post(self, path, data=None, token_path=None, **kwargs):
        payload = dict(data or {})
        payload.setdefault("csrf_token", self.token(token_path or path))
        return self.client.post(path, data=payload, **kwargs)

    def register(self, username="riya", password="secret123", path="/auth/register"):
        return self.post(
            path,
            {"username": username, "password": password, "confirm": password},
        )

    def login(self, username="riya", password="secret123", path="/auth/login"):
        return self.post(path, {"username": username, "password": password})

    def logout(self):
        return self.post("/auth/logout", {}, token_path="/expenses/")


@pytest.fixture()
def auth(client):
    return Auth(client)


@pytest.fixture()
def user(client, auth):
    """A registered and signed in user with the eight default categories."""
    response = auth.register()
    assert response.status_code == 302
    return response
