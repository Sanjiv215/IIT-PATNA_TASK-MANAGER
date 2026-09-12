"""
seed.py - Seeds the SQLite database with realistic initial student tasks.
Run this script with: python seed.py
"""

from database import get_db, init_db, DEFAULT_DB_PATH
import os

SAMPLE_TASKS = [
    {
        "title": "CS201 Data Structures Assignment",
        "description": "Implement a balanced Binary Search Tree in Python and write unit tests.",
        "priority": "High",
        "due_date": "2026-09-18",
        "status": "Pending"
    },
    {
        "title": "Physics Lab Report - Optics",
        "description": "Analyze diffraction grating data and submit the final 4-page PDF report.",
        "priority": "Medium",
        "due_date": "2026-09-20",
        "status": "Pending"
    },
    {
        "title": "Submit Scholarship Application",
        "description": "Attach transcripts and letter of recommendation before the deadline.",
        "priority": "High",
        "due_date": "2026-09-15",
        "status": "Pending"
    },
    {
        "title": "Buy Calculus Textbook",
        "description": "Purchase or rent Stewart Calculus 9th Edition from campus bookstore.",
        "priority": "Low",
        "due_date": "2026-09-25",
        "status": "Completed"
    },
    {
        "title": "English Literature Essay Outline",
        "description": "Draft a 1-page thesis outline on Shakespeare's Hamlet theme of vengeance.",
        "priority": "Low",
        "due_date": "2026-09-22",
        "status": "Pending"
    },
    {
        "title": "Register for Midterm Exam Slots",
        "description": "Log into the university portal and confirm exam center slot selections.",
        "priority": "Medium",
        "due_date": "2026-09-14",
        "status": "Completed"
    }
]


def seed_database(db_path=DEFAULT_DB_PATH):
    # Ensure tables exist
    init_db(db_path)
    conn = get_db(db_path)
    cursor = conn.cursor()

    # Clear existing tasks to avoid duplicate test entries on re-run
    cursor.execute("DELETE FROM tasks;")

    # Insert sample tasks with parameterized SQL to prevent SQL injection
    for task in SAMPLE_TASKS:
        cursor.execute(
            """
            INSERT INTO tasks (title, description, priority, due_date, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task["title"], task["description"], task["priority"], task["due_date"], task["status"])
        )

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM tasks;")
    count = cursor.fetchone()[0]
    conn.close()
    print(f"Successfully seeded database with {count} sample tasks at {db_path}!")


if __name__ == "__main__":
    seed_database()
