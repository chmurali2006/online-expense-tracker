import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA_FILE = Path(__file__).with_name("schema.sql")


def connect_to(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    # One connection per request, closed by close_db.
    if "db" not in g:
        g.db = connect_to(current_app.config["DATABASE"])
    return g.db


def close_db(exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(path):
    conn = connect_to(path)
    conn.executescript(SCHEMA_FILE.read_text())
    conn.commit()
    conn.close()
