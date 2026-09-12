"""
Pytest configuration and shared fixtures for testing Flask API.
Uses temporary SQLite database files per test session / module.
"""

import os
import tempfile
import pytest
from app import create_app
from database import init_db


@pytest.fixture
def app():
    """Create and configure a new Flask app instance for each test."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    app = create_app({
        "TESTING": True,
        "DATABASE": db_path,
        "SECRET_KEY": "test-secret-key"
    })

    with app.app_context():
        init_db(db_path)

    yield app

    # Cleanup temporary test database after test finishes
    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for making simulated HTTP requests to the application."""
    return app.test_client()
