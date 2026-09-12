"""
Pytest configuration and shared fixtures for testing Flask API with authentication.
"""

import os
import tempfile
import pytest
from app import create_app
from database import init_db
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    """Create and configure a new Flask app instance with a temporary SQLite database for each test."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    app = create_app({
        "TESTING": True,
        "DATABASE": db_path,
        "SECRET_KEY": "test-secret-key-student-task-manager",
    })

    with app.app_context():
        init_db(db_path)

    yield app

    # Cleanup temporary test database after test
    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def client(app):
    """Unauthenticated test client."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client):
    """Test client authenticated as a registered user (Student Alice)."""
    # Register and login user
    with client.session_transaction() as sess:
        # Create user directly in database
        with app.app_context():
            from database import get_db
            db = get_db(app.config["DATABASE"])
            cursor = db.cursor()
            pw_hash = generate_password_hash("Password123!")
            cursor.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                ("Student Alice", "alice@university.edu", pw_hash)
            )
            db.commit()
            user_id = cursor.lastrowid

        sess["user_id"] = user_id
        sess["user_name"] = "Student Alice"
        sess["user_email"] = "alice@university.edu"

    return client
