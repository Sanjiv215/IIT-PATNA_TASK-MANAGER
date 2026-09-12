"""
database.py - Database connection and initialization helper for SQLite.
Provides functions to connect to SQLite, execute schema migrations,
and convert rows into Python dictionaries.
"""

import sqlite3
import os
from flask import g, has_app_context

DATABASE_NAME = "tasks.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, DATABASE_NAME)
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def get_db(db_path=None):
    """
    Returns a database connection.
    If running within a Flask application context, it caches the connection on `g`.
    Uses sqlite3.Row so columns can be accessed by column name or converted to dict.
    """
    target_path = db_path or DEFAULT_DB_PATH

    if has_app_context():
        if 'db' not in g:
            g.db = sqlite3.connect(target_path)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db

    # Outside Flask application context (e.g. CLI, seed script, standalone tests)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def close_db(e=None):
    """Closes the active database connection in the Flask context if one exists."""
    if has_app_context():
        db = g.pop('db', None)
        if db is not None:
            db.close()


def init_db(db_path=None):
    """
    Initializes the database using schema.sql.
    Creates tables if they don't already exist.
    """
    conn = get_db(db_path)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    if not has_app_context():
        conn.close()


if __name__ == "__main__":
    print(f"Initializing database at: {DEFAULT_DB_PATH}")
    init_db()
    print("Database initialized successfully!")
