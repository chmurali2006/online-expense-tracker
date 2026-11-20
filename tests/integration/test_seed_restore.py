from werkzeug.security import generate_password_hash

from app import queries
from app.seed import reseed_demo_user, seed_demo_user


def test_reseed_restores_demo_data_and_leaves_other_users_alone(app):
    with app.app_context():
        seed_demo_user()
        demo = queries.get_user_by_username("demo")

        # Another user with real data that must survive the restore.
        other_id = queries.create_user("other", generate_password_hash("secret123"))
        queries.create_default_categories(other_id)
        other_category = queries.list_categories(other_id)[0]
        queries.insert_expense(other_id, {
            "category_id": other_category["id"],
            "amount": 75.0,
            "date": "2026-03-04",
            "payment_method": "cash",
            "note": "Keep me",
        })

        # Simulate the demo data being partly deleted.
        db = queries.get_db()
        with db:
            db.execute("DELETE FROM expenses WHERE user_id = ?", (demo["id"],))
            db.execute("DELETE FROM budgets WHERE user_id = ?", (demo["id"],))
            db.execute("DELETE FROM categories WHERE user_id = ?", (demo["id"],))

        created, message = reseed_demo_user()

        assert created
        assert "restored" in message
        assert "demo user" in message
        assert len(queries.list_categories(demo["id"])) == 8
        _, total = queries.list_expenses(demo["id"], per_page=0)
        assert 45 <= total <= 60
        other_rows, other_total = queries.list_expenses(other_id, per_page=0)
        assert other_total == 1
        assert other_rows[0]["note"] == "Keep me"
