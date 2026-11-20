-- Online Expense Tracker schema. Read and applied by app/db.py.

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, name)
);

CREATE TABLE IF NOT EXISTS expenses (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    category_id    INTEGER NOT NULL REFERENCES categories (id),
    amount         REAL    NOT NULL CHECK (amount > 0),
    date           TEXT    NOT NULL,
    payment_method TEXT    NOT NULL,
    note           TEXT    NOT NULL DEFAULT '',
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS budgets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories (id) ON DELETE CASCADE,
    month       TEXT    NOT NULL,
    amount      REAL    NOT NULL CHECK (amount > 0),
    UNIQUE (user_id, category_id, month)
);

-- Staged CSV imports live here, not in the session cookie, so a large file
-- does not overflow the 4 KB cookie limit between upload and preview.
CREATE TABLE IF NOT EXISTS import_batches (
    token      TEXT PRIMARY KEY,
    filename   TEXT NOT NULL,
    rows_json  TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Added in sprint 3 when the list page got slow with 5000 rows.
CREATE INDEX IF NOT EXISTS idx_expenses_user_date    ON expenses (user_id, date);
CREATE INDEX IF NOT EXISTS idx_expenses_user_amount  ON expenses (user_id, amount);
CREATE INDEX IF NOT EXISTS idx_expenses_user_method  ON expenses (user_id, payment_method);
CREATE INDEX IF NOT EXISTS idx_expenses_user_cat     ON expenses (user_id, category_id);
CREATE INDEX IF NOT EXISTS idx_budgets_user_month    ON budgets (user_id, month);
