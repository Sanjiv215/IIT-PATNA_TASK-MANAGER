"""
reset_db.py - Wipes all records from the SQLite database, leaving 0 rows
while keeping tables, schema, constraints, and indexes intact.
Run with: python reset_db.py
"""

import sqlite3
import os
from database import get_db, init_db, DEFAULT_DB_PATH


def reset_database(db_path=DEFAULT_DB_PATH):
    # Ensure schema is initialized first
    init_db(db_path)
    
    conn = get_db(db_path)
    cursor = conn.cursor()

    # Disable foreign keys temporarily during wipe to avoid constraint order issues
    cursor.execute("PRAGMA foreign_keys = OFF;")
    
    # Delete all rows
    cursor.execute("DELETE FROM tasks;")
    cursor.execute("DELETE FROM users;")

    # Reset SQLite autoincrement sequence counters
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('tasks', 'users');")

    # Re-enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON;")
    conn.commit()

    # Verify zero data
    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tasks;")
    task_count = cursor.fetchone()[0]

    conn.close()

    print("=" * 50)
    print("✨ Database Reset Complete (Zero Data)")
    print("=" * 50)
    print(f"Database File : {db_path}")
    print(f"Total Users   : {user_count} rows")
    print(f"Total Tasks   : {task_count} rows")
    print("All tables and indexes are intact and ready for a fresh signup.")
    print("=" * 50)


if __name__ == "__main__":
    reset_database()
