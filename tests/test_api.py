"""
Comprehensive tests for Student Task Manager:
- Authentication (Signup, Login, Logout, Validation)
- Route Protection & User Data Isolation
- Task CRUD, Search, and Filtering
"""

import json


# -----------------------------------------------------------------
# 1. Authentication Tests
# -----------------------------------------------------------------

def test_signup_success(client):
    """Test successful user registration via JSON and session creation."""
    payload = {
        "name": "Jane Doe",
        "email": "jane@university.edu",
        "password": "StrongPassword123",
        "confirm_password": "StrongPassword123"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert "user" in data
    assert data["user"]["email"] == "jane@university.edu"

    # Verify session is established
    me_res = client.get("/api/me")
    assert me_res.status_code == 200
    assert me_res.get_json()["email"] == "jane@university.edu"


def test_signup_validation_missing_name(client):
    """Test signup fails when name is missing."""
    payload = {
        "name": "",
        "email": "noname@university.edu",
        "password": "Password123",
        "confirm_password": "Password123"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 400
    assert "name is required" in response.get_json()["error"].lower()


def test_signup_validation_invalid_email(client):
    """Test signup fails when email is malformed."""
    payload = {
        "name": "Alex",
        "email": "not-an-email",
        "password": "Password123",
        "confirm_password": "Password123"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 400
    assert "valid email" in response.get_json()["error"].lower()


def test_signup_validation_short_password(client):
    """Test signup fails when password is less than 8 characters."""
    payload = {
        "name": "Alex",
        "email": "alex@university.edu",
        "password": "short",
        "confirm_password": "short"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 400
    assert "8 characters" in response.get_json()["error"].lower()


def test_signup_validation_password_mismatch(client):
    """Test signup fails when passwords do not match."""
    payload = {
        "name": "Alex",
        "email": "alex@university.edu",
        "password": "Password123",
        "confirm_password": "PasswordMismatch"
    }
    response = client.post("/signup", json=payload)
    assert response.status_code == 400
    assert "do not match" in response.get_json()["error"].lower()


def test_signup_validation_duplicate_email(client):
    """Test signup fails when email is already registered."""
    payload = {
        "name": "User One",
        "email": "duplicate@university.edu",
        "password": "Password123",
        "confirm_password": "Password123"
    }
    res1 = client.post("/signup", json=payload)
    assert res1.status_code == 201

    # Second signup attempt with same email
    res2 = client.post("/signup", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.get_json()["error"].lower()


def test_login_success_and_logout(client):
    """Test login with valid credentials and subsequent logout."""
    # Register first
    client.post("/signup", json={
        "name": "Bob Smith",
        "email": "bob@university.edu",
        "password": "SecretPassword123",
        "confirm_password": "SecretPassword123"
    })
    client.get("/logout")  # Log out

    # Log back in
    login_res = client.post("/login", json={
        "email": "bob@university.edu",
        "password": "SecretPassword123"
    })
    assert login_res.status_code == 200
    assert login_res.get_json()["user"]["email"] == "bob@university.edu"

    # Verify active session
    me_res = client.get("/api/me")
    assert me_res.status_code == 200

    # Logout
    logout_res = client.get("/logout")
    assert logout_res.status_code == 302  # redirects to /login

    # After logout, /api/me should be unauthorized
    unauth_res = client.get("/api/me")
    assert unauth_res.status_code == 401


def test_login_invalid_credentials(client):
    """Test login rejection on wrong password or unregistered email."""
    # Non-existent user
    res1 = client.post("/login", json={"email": "nobody@test.com", "password": "Password123"})
    assert res1.status_code == 401

    # Register user
    client.post("/signup", json={
        "name": "User",
        "email": "user@test.com",
        "password": "CorrectPassword123",
        "confirm_password": "CorrectPassword123"
    })
    client.get("/logout")

    # Incorrect password
    res2 = client.post("/login", json={"email": "user@test.com", "password": "WrongPassword"})
    assert res2.status_code == 401


# -----------------------------------------------------------------
# 2. Route Protection & User Isolation Tests
# -----------------------------------------------------------------

def test_unauthenticated_api_protection(client):
    """Test that all task API endpoints return 401 Unauthorized when unauthenticated."""
    assert client.get("/api/tasks").status_code == 401
    assert client.post("/api/tasks", json={"title": "Test"}).status_code == 401
    assert client.get("/api/tasks/1").status_code == 401
    assert client.put("/api/tasks/1", json={"title": "Test"}).status_code == 401
    assert client.patch("/api/tasks/1/complete").status_code == 401
    assert client.delete("/api/tasks/1").status_code == 401
    assert client.get("/api/tasks/search?q=test").status_code == 401


def test_user_data_isolation(app, client):
    """
    Test strict user isolation:
    User A cannot view, edit, complete, or delete User B's tasks.
    """
    # 1. Register User A and create a task
    client.post("/signup", json={
        "name": "User A",
        "email": "usera@test.com",
        "password": "Password123",
        "confirm_password": "Password123"
    })
    task_res = client.post("/api/tasks", json={"title": "User A Secret Assignment", "priority": "High"})
    task_a_id = task_res.get_json()["task"]["id"]

    # 2. Register User B
    client.get("/logout")
    client.post("/signup", json={
        "name": "User B",
        "email": "userb@test.com",
        "password": "Password123",
        "confirm_password": "Password123"
    })

    # 3. User B lists tasks -> should be empty
    list_res = client.get("/api/tasks")
    assert list_res.status_code == 200
    assert len(list_res.get_json()) == 0

    # 4. User B tries to get User A's task -> 404
    assert client.get(f"/api/tasks/{task_a_id}").status_code == 404

    # 5. User B tries to update User A's task -> 404
    assert client.put(f"/api/tasks/{task_a_id}", json={"title": "Hacked Title"}).status_code == 404

    # 6. User B tries to complete User A's task -> 404
    assert client.patch(f"/api/tasks/{task_a_id}/complete").status_code == 404

    # 7. User B tries to delete User A's task -> 404
    assert client.delete(f"/api/tasks/{task_a_id}").status_code == 404

    # 8. User B searches -> does not see User A's task
    search_res = client.get("/api/tasks/search?q=Secret")
    assert search_res.status_code == 200
    assert len(search_res.get_json()) == 0


# -----------------------------------------------------------------
# 3. Task Management CRUD & Validation Tests (Authenticated)
# -----------------------------------------------------------------

def test_create_task_authenticated(auth_client):
    """Test creating a task under an authenticated session."""
    payload = {
        "title": "Math Homework 1",
        "description": "Exercises 1-10",
        "priority": "High",
        "due_date": "2026-10-15"
    }
    res = auth_client.post("/api/tasks", json=payload)
    assert res.status_code == 201
    task = res.get_json()["task"]
    assert task["title"] == "Math Homework 1"
    assert task["priority"] == "High"
    assert task["status"] == "Pending"


def test_task_validation_errors(auth_client):
    """Test server-side validation for task creation."""
    # Missing title
    assert auth_client.post("/api/tasks", json={"title": ""}).status_code == 400
    # Invalid priority
    assert auth_client.post("/api/tasks", json={"title": "T", "priority": "Urgent"}).status_code == 400
    # Invalid date
    assert auth_client.post("/api/tasks", json={"title": "T", "due_date": "invalid-date"}).status_code == 400


def test_update_and_toggle_complete(auth_client):
    """Test updating task details and toggling completion."""
    create_res = auth_client.post("/api/tasks", json={"title": "Physics Quiz", "priority": "Medium"})
    task_id = create_res.get_json()["task"]["id"]

    # Update
    update_res = auth_client.put(f"/api/tasks/{task_id}", json={
        "title": "Physics Final Exam",
        "priority": "High",
        "description": "Covers chapters 1-8"
    })
    assert update_res.status_code == 200
    assert update_res.get_json()["task"]["title"] == "Physics Final Exam"

    # Toggle Complete
    patch_res = auth_client.patch(f"/api/tasks/{task_id}/complete")
    assert patch_res.status_code == 200
    assert patch_res.get_json()["task"]["status"] == "Completed"


def test_delete_task_authenticated(auth_client):
    """Test deleting task."""
    create_res = auth_client.post("/api/tasks", json={"title": "Delete Me", "priority": "Low"})
    task_id = create_res.get_json()["task"]["id"]

    del_res = auth_client.delete(f"/api/tasks/{task_id}")
    assert del_res.status_code == 200
    assert auth_client.get(f"/api/tasks/{task_id}").status_code == 404


def test_filter_and_search_tasks(auth_client):
    """Test query filtering and keyword search."""
    auth_client.post("/api/tasks", json={"title": "Algorithms HW", "priority": "High", "status": "Pending"})
    auth_client.post("/api/tasks", json={"title": "History Reading", "priority": "Low", "status": "Completed"})

    # Filter status
    res_pending = auth_client.get("/api/tasks?status=Pending")
    assert res_pending.status_code == 200
    assert all(t["status"] == "Pending" for t in res_pending.get_json())

    # Filter priority
    res_high = auth_client.get("/api/tasks?priority=High")
    assert res_high.status_code == 200
    assert all(t["priority"] == "High" for t in res_high.get_json())

    # Search
    search_res = auth_client.get("/api/tasks/search?q=Algorithms")
    assert search_res.status_code == 200
    assert len(search_res.get_json()) == 1
    assert search_res.get_json()[0]["title"] == "Algorithms HW"
