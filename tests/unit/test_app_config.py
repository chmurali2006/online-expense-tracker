def test_secret_key_is_set_and_stable_without_explicit_config(tmp_path):
    from app import create_app

    one = create_app({"DATABASE": str(tmp_path / "one.sqlite3")})
    two = create_app({"DATABASE": str(tmp_path / "two.sqlite3")})

    assert one.config["SECRET_KEY"]
    assert one.config["SECRET_KEY"] == two.config["SECRET_KEY"]
