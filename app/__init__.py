import os
import secrets
from pathlib import Path

from flask import Flask, Response, abort, g, render_template, request, session

from app import db as db_module
from app.format import format_inr, format_percent, format_signed
from app.queries import get_user_by_id


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.environ.get("DATABASE") or str(Path(app.instance_path) / "expense_tracker.sqlite3"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=512 * 1024,
        PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 14,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if os.environ.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    elif not app.config.get("SECRET_KEY"):
        # A stable key per install keeps sessions alive across restarts.
        key_file = Path(app.instance_path) / "secret_key.txt"
        if key_file.exists():
            app.config["SECRET_KEY"] = key_file.read_text().strip()
        else:
            app.config["SECRET_KEY"] = "dev-" + secrets.token_hex(16)
            key_file.write_text(app.config["SECRET_KEY"])
    db_module.init_db(app.config["DATABASE"])
    app.teardown_appcontext(db_module.close_db)

    # Imported here so the route modules can import helpers from this package.
    from app.routes import auth, budgets, categories, dashboard, data, expenses

    app.register_blueprint(auth.bp)
    app.register_blueprint(expenses.bp)
    app.register_blueprint(categories.bp)
    app.register_blueprint(budgets.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(data.bp)

    @app.before_request
    def load_user_and_check_csrf():
        user_id = session.get("user_id")
        g.user = get_user_by_id(user_id) if user_id else None
        if request.method == "POST":
            token = request.form.get("csrf_token")
            if not token or token != session.get("csrf_token"):
                abort(400)

    def csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(16)
        return session["csrf_token"]

    @app.context_processor
    def inject_globals():
        return {
            "user": g.get("user"),
            "csrf_token": csrf_token,
            "format_inr": format_inr,
            "format_signed": format_signed,
            "format_percent": format_percent,
            "payment_methods": ["cash", "UPI", "card", "bank"],
            "current_month": now_month(),
            "fmt1": lambda value: f"{value:.1f}",
        }

    @app.route("/robots.txt")
    def robots_txt():
        return Response("User-agent: *\nAllow: /\n", mimetype="text/plain")

    @app.errorhandler(404)
    def not_found(exc):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(exc):
        app.logger.exception("500 error")
        return render_template("errors/500.html"), 500

    @app.errorhandler(400)
    def bad_request(exc):
        return render_template("errors/400.html"), 400

    @app.cli.command("init-db")
    def init_db_command():
        db_module.init_db(app.config["DATABASE"])
        print("Database created.")

    @app.cli.command("seed")
    def seed_command():
        from app.seed import seed_demo_user

        created, message = seed_demo_user()
        print(message)

    @app.cli.command("reseed-demo")
    def reseed_demo_command():
        """Restore the demo account's sample data without touching other users."""
        from app.seed import reseed_demo_user

        created, message = reseed_demo_user()
        print(message)

    return app


def now_month():
    from datetime import date

    return date.today().strftime("%Y-%m")
