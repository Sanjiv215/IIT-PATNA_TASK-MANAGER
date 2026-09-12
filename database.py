"""
database.py - Database connection, initialization, and migration helper for SQLite.
Manages connections, schema migrations, and user data isolation.
"""

import sqlite3
import os
from flask import g, has_app_context
from werkzeug.security import generate_password_hash

DATABASE_NAME = "tasks.db"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, DATABASE_NAME)
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def get_db(db_path=None):
    """
    Returns a database connection with foreign key enforcement and row factory.
    If running within a Flask application context, caches connection on `g`.
    """
    target_path = db_path or DEFAULT_DB_PATH

    if has_app_context():
        if 'db' not in g:
            g.db = sqlite3.connect(target_path)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db

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


def migrate_schema_if_needed(conn):
    """
    Checks if an existing database needs table creation or column migrations.
    """
    cursor = conn.cursor()
    
    # 1. Create users table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Check if tasks table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks';")
    tasks_exists = cursor.fetchone() is not None

    if not tasks_exists:
        # Create full tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                priority TEXT NOT NULL CHECK(priority IN ('Low', 'Medium', 'High')) DEFAULT 'Medium',
                due_date TEXT,
                status TEXT NOT NULL CHECK(status IN ('Pending', 'Completed')) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        # Check if user_id column exists
        cursor.execute("PRAGMA table_info(tasks);")
        columns = [row["name"] for row in cursor.fetchall()]
        if "user_id" not in columns:
            # Ensure demo user exists
            demo_email = "demo@student.edu"
            cursor.execute("SELECT id FROM users WHERE email = ?", (demo_email,))
            user_row = cursor.fetchone()
            if user_row is None:
                demo_hash = generate_password_hash("Password123!")
                cursor.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    ("Demo Student", demo_email, demo_hash)
                )
                demo_user_id = cursor.lastrowid
            else:
                demo_user_id = user_row["id"]

            cursor.execute("ALTER TABLE tasks ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;")
            cursor.execute("UPDATE tasks SET user_id = ? WHERE user_id IS NULL;", (demo_user_id,))

    # 3. Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);")
    conn.commit()


def init_db(db_path=None):
    """
    Initializes the database schema and applies any migrations.
    """
    conn = get_db(db_path)
    migrate_schema_if_needed(conn)
    if not has_app_context():
        conn.close()


if __name__ == "__main__":
    print(f"Initializing and migrating database at: {DEFAULT_DB_PATH}")
    init_db()
    print("Database initialized successfully!")
