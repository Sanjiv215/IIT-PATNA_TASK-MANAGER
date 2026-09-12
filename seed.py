"""
seed.py - Seeds the SQLite database with initial user account and sample student tasks.
Run this script with: python seed.py
"""

from datetime import datetime, timedelta
from database import get_db, init_db, DEFAULT_DB_PATH
from werkzeug.security import generate_password_hash

DEMO_USER = {
    "name": "Demo Student",
    "email": "demo@student.edu",
    "password": "Password123!"
}

today = datetime.now()


def days_ago(d):
    return (today - timedelta(days=d)).strftime("%Y-%m-%d %H:%M:%S")


def future_date(d):
    return (today + timedelta(days=d)).strftime("%Y-%m-%d")


SAMPLE_TASKS = [
    {
        "title": "CS201 Data Structures Assignment",
        "description": "Implement a balanced Binary Search Tree in Python and write unit tests.",
        "priority": "High",
        "due_date": future_date(2),
        "status": "Pending",
        "reminder_offset": "1_day_before",
        "completed_at": None
    },
    {
        "title": "Physics Lab Report - Optics",
        "description": "Analyze diffraction grating data and submit the final 4-page PDF report.",
        "priority": "Medium",
        "due_date": future_date(4),
        "status": "Pending",
        "reminder_offset": "same_day",
        "completed_at": None
    },
    {
        "title": "Submit Scholarship Application",
        "description": "Attach transcripts and letter of recommendation before the deadline.",
        "priority": "High",
        "due_date": future_date(0),  # Due today
        "status": "Pending",
        "reminder_offset": "same_day",
        "completed_at": None
    },
    {
        "title": "Buy Calculus Textbook",
        "description": "Purchase or rent Stewart Calculus 9th Edition from campus bookstore.",
        "priority": "Low",
        "due_date": future_date(10),
        "status": "Completed",
        "reminder_offset": "none",
        "completed_at": days_ago(0)
    },
    {
        "title": "English Literature Essay Outline",
        "description": "Draft a 1-page thesis outline on Shakespeare's Hamlet theme of vengeance.",
        "priority": "Low",
        "due_date": future_date(6),
        "status": "Pending",
        "reminder_offset": "none",
        "completed_at": None
    },
    {
        "title": "Register for Midterm Exam Slots",
        "description": "Log into the university portal and confirm exam center slot selections.",
        "priority": "Medium",
        "due_date": days_ago(1)[:10],
        "status": "Completed",
        "reminder_offset": "none",
        "completed_at": days_ago(1)
    },
    {
        "title": "Linear Algebra Problem Set 3",
        "description": "Solve matrix diagonalization and eigenvector questions.",
        "priority": "High",
        "due_date": days_ago(2)[:10],
        "status": "Completed",
        "reminder_offset": "none",
        "completed_at": days_ago(2)
    },
    {
        "title": "History Reading Quiz Prep",
        "description": "Read Chapter 12 on Industrial Revolution.",
        "priority": "Medium",
        "due_date": days_ago(3)[:10],
        "status": "Completed",
        "reminder_offset": "none",
        "completed_at": days_ago(3)
    }
]


def seed_database(db_path=DEFAULT_DB_PATH):
    init_db(db_path)
    conn = get_db(db_path)
    cursor = conn.cursor()

    # 1. Create or retrieve demo user
    cursor.execute("SELECT id FROM users WHERE email = ?", (DEMO_USER["email"],))
    user_row = cursor.fetchone()
    if user_row is None:
        pw_hash = generate_password_hash(DEMO_USER["password"])
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (DEMO_USER["name"], DEMO_USER["email"], pw_hash)
        )
        user_id = cursor.lastrowid
    else:
        user_id = user_row["id"]

    # 2. Clear demo user's existing tasks to avoid duplicate test entries on re-run
    cursor.execute("DELETE FROM tasks WHERE user_id = ?;", (user_id,))

    # 3. Insert sample tasks with parameterized SQL
    for task in SAMPLE_TASKS:
        cursor.execute(
            """
            INSERT INTO tasks (user_id, title, description, priority, due_date, status, reminder_offset, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, task["title"], task["description"], task["priority"], task["due_date"], task["status"], task["reminder_offset"], task["completed_at"])
        )

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ?;", (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    print(f"Successfully seeded database with {count} sample tasks for user '{DEMO_USER['email']}' at {db_path}!")


if __name__ == "__main__":
    seed_database()
