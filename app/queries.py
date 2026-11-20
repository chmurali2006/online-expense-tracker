"""Every SQL statement in the project lives in this file.

Plain functions, one connection handed in from app.db, no classes.
"""

from app.db import get_db
from app.services.validation import PAYMENT_METHODS

DEFAULT_CATEGORY_NAMES = [
    "Food",
    "Travel",
    "Groceries",
    "Rent",
    "Utilities",
    "Stationery",
    "Health",
    "Entertainment",
]

SORT_COLUMNS = {"date": "e.date", "amount": "e.amount"}


def _all(cursor):
    return [dict(row) for row in cursor.fetchall()]


def _one(cursor):
    row = cursor.fetchone()
    return dict(row) if row else None


# ---- users -----------------------------------------------------------------

def create_user(username, password_hash):
    cur = get_db().execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash),
    )
    get_db().commit()
    return cur.lastrowid


def get_user_by_username(username):
    return _one(get_db().execute("SELECT * FROM users WHERE username = ?", (username,)))


def get_user_by_id(user_id):
    return _one(get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)))


def update_password(user_id, password_hash):
    get_db().execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
    get_db().commit()


# ---- categories ------------------------------------------------------------

def create_default_categories(user_id):
    db = get_db()
    db.executemany(
        "INSERT INTO categories (user_id, name, is_default) VALUES (?, ?, 1)",
        [(user_id, name) for name in DEFAULT_CATEGORY_NAMES],
    )
    db.commit()


def list_categories(user_id):
    return _all(
        get_db().execute(
            "SELECT * FROM categories WHERE user_id = ? ORDER BY is_default DESC, name",
            (user_id,),
        )
    )


def get_category(user_id, category_id):
    return _one(
        get_db().execute(
            "SELECT * FROM categories WHERE id = ? AND user_id = ?",
            (category_id, user_id),
        )
    )


def get_category_by_name(user_id, name):
    return _one(
        get_db().execute(
            "SELECT * FROM categories WHERE user_id = ? AND lower(name) = lower(?)",
            (user_id, name),
        )
    )


def insert_category(user_id, name):
    cur = get_db().execute(
        "INSERT INTO categories (user_id, name) VALUES (?, ?)",
        (user_id, name),
    )
    get_db().commit()
    return cur.lastrowid


def rename_category(user_id, category_id, name):
    get_db().execute(
        "UPDATE categories SET name = ? WHERE id = ? AND user_id = ?",
        (name, category_id, user_id),
    )
    get_db().commit()


def delete_category(user_id, category_id):
    get_db().execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (category_id, user_id))
    get_db().commit()


def count_category_expenses(category_id, user_id):
    row = get_db().execute(
        "SELECT COUNT(*) AS n FROM expenses WHERE category_id = ? AND user_id = ?",
        (category_id, user_id),
    ).fetchone()
    return row["n"]


def move_category_expenses(from_id, to_id, user_id):
    # Called before the delete, one statement and one commit.
    db = get_db()
    db.execute(
        "UPDATE expenses SET category_id = ? WHERE category_id = ? AND user_id = ?",
        (to_id, from_id, user_id),
    )
    db.commit()


def categories_with_counts(user_id):
    return _all(
        get_db().execute(
            """
            SELECT c.id, c.name, c.is_default,
                   (SELECT COUNT(*) FROM expenses e
                     WHERE e.category_id = c.id AND e.user_id = c.user_id) AS expense_count
              FROM categories c
             WHERE c.user_id = ?
             ORDER BY c.is_default DESC, c.name
            """,
            (user_id,),
        )
    )


# ---- expenses --------------------------------------------------------------

EXPENSE_SELECT = """
    SELECT e.id, e.user_id, e.amount, e.date, e.payment_method, e.note,
           e.category_id, e.created_at, c.name AS category_name
      FROM expenses e
      JOIN categories c ON c.id = e.category_id
"""


def _expense_where(user_id, date_from, date_to, category_id, method, q):
    sql = " WHERE e.user_id = ?"
    params = [user_id]
    if date_from:
        sql += " AND e.date >= ?"
        params.append(date_from)
    if date_to:
        sql += " AND e.date <= ?"
        params.append(date_to)
    if category_id:
        sql += " AND e.category_id = ?"
        params.append(int(category_id))
    if method:
        sql += " AND e.payment_method = ?"
        params.append(method)
    if q:
        sql += " AND e.note LIKE ?"
        params.append(f"%{q}%")
    return sql, params


def list_expenses(
    user_id,
    date_from=None,
    date_to=None,
    category_id=None,
    method=None,
    q=None,
    sort="date",
    direction="desc",
    page=1,
    per_page=15,
):
    """Returns (rows, total matching rows). per_page=0 means no LIMIT, used by the CSV export."""
    where, params = _expense_where(user_id, date_from, date_to, category_id, method, q)
    db = get_db()
    total = db.execute("SELECT COUNT(*) AS n FROM expenses e" + where, params).fetchone()["n"]

    column = SORT_COLUMNS.get(sort, "e.date")
    order = "ASC" if direction == "asc" else "DESC"
    sql = EXPENSE_SELECT + where + f" ORDER BY {column} {order}, e.id {order}"
    if per_page:
        offset = max(page - 1, 0) * per_page
        sql += " LIMIT ? OFFSET ?"
        params = params + [per_page, offset]

    return _all(db.execute(sql, params)), total


def get_expense(user_id, expense_id):
    return _one(
        get_db().execute(EXPENSE_SELECT + " WHERE e.id = ? AND e.user_id = ?", (expense_id, user_id))
    )


def insert_expense(user_id, data):
    cur = get_db().execute(
        """
        INSERT INTO expenses (user_id, category_id, amount, date, payment_method, note)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, data["category_id"], data["amount"], data["date"], data["payment_method"], data["note"]),
    )
    get_db().commit()
    return cur.lastrowid


def update_expense(user_id, expense_id, data):
    get_db().execute(
        """
        UPDATE expenses
           SET category_id = ?, amount = ?, date = ?, payment_method = ?, note = ?
         WHERE id = ? AND user_id = ?
        """,
        (
            data["category_id"],
            data["amount"],
            data["date"],
            data["payment_method"],
            data["note"],
            expense_id,
            user_id,
        ),
    )
    get_db().commit()


def insert_expenses(user_id, rows):
    """Insert a whole staged import in one transaction, or none of it."""
    values = [
        (
            user_id,
            row["category_id"],
            row["amount"],
            row["date"],
            row["payment_method"],
            row["note"],
        )
        for row in rows
    ]
    db = get_db()
    try:
        db.executemany(
            """
            INSERT INTO expenses (user_id, category_id, amount, date, payment_method, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


def delete_expense(user_id, expense_id):
    get_db().execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    get_db().commit()


def recent_expenses(user_id, limit=5):
    return _all(
        get_db().execute(
            EXPENSE_SELECT + " WHERE e.user_id = ? ORDER BY e.date DESC, e.id DESC LIMIT ?",
            (user_id, limit),
        )
    )


# ---- staged CSV imports ----------------------------------------------------

def create_import_batch(token, filename, rows_json):
    get_db().execute(
        "INSERT INTO import_batches (token, filename, rows_json) VALUES (?, ?, ?)",
        (token, filename, rows_json),
    )
    get_db().commit()


def get_import_batch(token):
    return _one(get_db().execute("SELECT * FROM import_batches WHERE token = ?", (token,)))


def delete_import_batch(token):
    get_db().execute("DELETE FROM import_batches WHERE token = ?", (token,))
    get_db().commit()


# ---- budgets ---------------------------------------------------------------

def set_budget(user_id, category_id, month, amount):
    get_db().execute(
        """
        INSERT INTO budgets (user_id, category_id, month, amount) VALUES (?, ?, ?, ?)
        ON CONFLICT (user_id, category_id, month) DO UPDATE SET amount = excluded.amount
        """,
        (user_id, category_id, month, amount),
    )
    get_db().commit()


def delete_budget(user_id, budget_id):
    get_db().execute("DELETE FROM budgets WHERE id = ? AND user_id = ?", (budget_id, user_id))
    get_db().commit()


def budgets_for_month(user_id, month):
    """Budget rows for a month joined with what was actually spent in it."""
    return _all(
        get_db().execute(
            """
            SELECT b.id, b.category_id, b.month, b.amount AS budget,
                   c.name AS category_name,
                   COALESCE((SELECT SUM(e.amount) FROM expenses e
                              WHERE e.user_id = b.user_id
                                AND e.category_id = b.category_id
                                AND e.date LIKE ?), 0) AS spent
              FROM budgets b
              JOIN categories c ON c.id = b.category_id
             WHERE b.user_id = ? AND b.month = ?
             ORDER BY c.name
            """,
            (month + "%", user_id, month),
        )
    )


def category_spending(user_id, month):
    """All categories with their total for a month, including zero ones."""
    return _all(
        get_db().execute(
            """
            SELECT c.id, c.name,
                   COALESCE((SELECT SUM(e.amount) FROM expenses e
                              WHERE e.user_id = c.user_id
                                AND e.category_id = c.id
                                AND e.date LIKE ?), 0) AS spent
              FROM categories c
             WHERE c.user_id = ?
             ORDER BY c.name
            """,
            (month + "%", user_id),
        )
    )


# ---- dashboard summary -----------------------------------------------------

def month_total(user_id, month):
    row = get_db().execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE user_id = ? AND date LIKE ?",
        (user_id, month + "%"),
    ).fetchone()
    return row["total"]


def month_category_totals(user_id, month):
    return _all(
        get_db().execute(
            """
            SELECT c.name, SUM(e.amount) AS total
              FROM expenses e
              JOIN categories c ON c.id = e.category_id
             WHERE e.user_id = ? AND e.date LIKE ?
             GROUP BY c.id
             ORDER BY total DESC
            """,
            (user_id, month + "%"),
        )
    )


def month_daily_totals(user_id, month):
    return _all(
        get_db().execute(
            """
            SELECT substr(date, 9, 2) AS day, SUM(amount) AS total
              FROM expenses
             WHERE user_id = ? AND date LIKE ?
             GROUP BY day
             ORDER BY day
            """,
            (user_id, month + "%"),
        )
    )


def month_has_data(user_id, month):
    row = get_db().execute(
        "SELECT COUNT(*) AS n FROM expenses WHERE user_id = ? AND date LIKE ?",
        (user_id, month + "%"),
    ).fetchone()
    return row["n"] > 0


def first_expense_month(user_id):
    row = get_db().execute(
        "SELECT MIN(date) AS d FROM expenses WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row["d"][:7] if row and row["d"] else None
