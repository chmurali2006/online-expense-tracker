from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app import queries
from app.services.validation import validate_login, validate_password_change, validate_register

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods=("GET", "POST"))
def register():
    errors = {}
    username = ""
    if request.method == "POST":
        username, errors = validate_register(
            request.form.get("username"),
            request.form.get("password"),
            request.form.get("confirm"),
        )
        if not errors and queries.get_user_by_username(username):
            errors["username"] = "Username already taken"

        if not errors:
            user_id = queries.create_user(username, generate_password_hash(request.form.get("password")))
            queries.create_default_categories(user_id)
            session.clear()
            session["user_id"] = user_id
            session.permanent = True
            flash("Account created")
            return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html", errors=errors, username=username)


@bp.route("/login", methods=("GET", "POST"))
def login():
    errors = {}
    username = ""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        errors = validate_login(username, request.form.get("password"))
        if not errors:
            found = queries.get_user_by_username(username)
            if found and check_password_hash(found["password_hash"], request.form.get("password")):
                session.clear()
                session["user_id"] = found["id"]
                session.permanent = True
                flash("Signed in")
                target = request.args.get("next", "")
                # A backslash can be normalised to '/' by browsers, turning
                # "/\evil.test" into a protocol-relative external URL.
                if (
                    target.startswith("/")
                    and not target.startswith("//")
                    and "\\" not in target
                    and "\r" not in target
                    and "\n" not in target
                ):
                    return redirect(target)
                return redirect(url_for("dashboard.index"))
            errors["password"] = "Wrong username or password"

    return render_template("auth/login.html", errors=errors, username=username)


@bp.post("/logout")
def logout():
    session.clear()
    flash("Signed out")
    return redirect(url_for("auth.login"))


@bp.route("/change-password", methods=("GET", "POST"))
def change_password():
    if g.user is None:
        return redirect(url_for("auth.login", next=request.path))

    errors = {}
    if request.method == "POST":
        errors = validate_password_change(
            request.form.get("current"),
            request.form.get("new"),
            request.form.get("confirm"),
        )
        if not errors and not check_password_hash(g.user["password_hash"], request.form.get("current")):
            errors["current"] = "Current password is wrong"
        if not errors:
            queries.update_password(g.user["id"], generate_password_hash(request.form.get("new")))
            flash("Password changed")
            return redirect(url_for("dashboard.index"))

    return render_template("auth/change_password.html", errors=errors)
