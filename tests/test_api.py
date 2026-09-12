"""
Comprehensive tests for Student Task Manager:
- Authentication (Signup, Login, Logout, Validation)
- Route Protection & User Data Isolation
- Task CRUD, Search, and Filtering
- Part A: Personalized Progress Tracking (/api/progress)
- Part B: Monthly Calendar View (/api/tasks/calendar)
- Part C: Task Reminders (/api/reminders)
"""

from datetime import datetime, timedelta
import json


# -----------------------------------------------------------------
# 1. Authentication Tests
# -----------------------------------------------------------------

def test_signup_success(client):
    """Test successful user registration and session establishment."""
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

    me_res = client.get("/api/me")
    assert me_res.status_code == 200
    assert me_res.get_json()["email"] == "jane@university.edu"


def test_signup_validation_errors(client):
    """Test signup failure cases."""
    # Missing name
    res1 = client.post("/signup", json={"name": "", "email": "a@u.edu", "password": "Password123", "confirm_password": "Password123"})
    assert res1.status_code == 400

    # Invalid email
    res2 = client.post("/signup", json={"name": "A", "email": "bad-email", "password": "Password123", "confirm_password": "Password123"})
    assert res2.status_code == 400

    # Short password
    res3 = client.post("/signup", json={"name": "A", "email": "a@u.edu", "password": "short", "confirm_password": "short"})
    assert res3.status_code == 400

    # Password mismatch
    res4 = client.post("/signup", json={"name": "A", "email": "a@u.edu", "password": "Password123", "confirm_password": "MismatchPassword"})
    assert res4.status_code == 400


def test_login_success_and_logout(client):
    """Test login with valid credentials and logout."""
    client.post("/signup", json={
        "name": "Bob Smith",
        "email": "bob@university.edu",
        "password": "SecretPassword123",
        "confirm_password": "SecretPassword123"
    })
    client.get("/logout")

    login_res = client.post("/login", json={"email": "bob@university.edu", "password": "SecretPassword123"})
    assert login_res.status_code == 200

    logout_res = client.get("/logout")
    assert logout_res.status_code == 302
    assert client.get("/api/me").status_code == 401


# -----------------------------------------------------------------
# 2. Route Protection & User Isolation Tests
# -----------------------------------------------------------------

def test_unauthenticated_api_protection(client):
    """Test that all API routes require authentication."""
    assert client.get("/api/tasks").status_code == 401
    assert client.post("/api/tasks", json={"title": "T"}).status_code == 401
    assert client.get("/api/progress").status_code == 401
    assert client.get("/api/tasks/calendar").status_code == 401
    assert client.get("/api/reminders").status_code == 401


def test_user_data_isolation(client):
    """Test that User B cannot access or modify User A's coursework."""
    # User A creates a task
    client.post("/signup", json={"name": "User A", "email": "a@test.com", "password": "Password123", "confirm_password": "Password123"})
    res = client.post("/api/tasks", json={"title": "User A Secret", "priority": "High"})
    task_a_id = res.get_json()["task"]["id"]

    # User B registers
    client.get("/logout")
    client.post("/signup", json={"name": "User B", "email": "b@test.com", "password": "Password123", "confirm_password": "Password123"})

    # User B checks list & search
    assert len(client.get("/api/tasks").get_json()) == 0
    assert len(client.get("/api/tasks/search?q=Secret").get_json()) == 0
    assert client.get(f"/api/tasks/{task_a_id}").status_code == 404
    assert client.put(f"/api/tasks/{task_a_id}", json={"title": "Hacked"}).status_code == 404
    assert client.delete(f"/api/tasks/{task_a_id}").status_code == 404


# -----------------------------------------------------------------
# 3. Task CRUD & Validation Tests
# -----------------------------------------------------------------

def test_task_crud_lifecycle(auth_client):
    """Test creating, updating, completing, and deleting tasks."""
    create_res = auth_client.post("/api/tasks", json={
        "title": "Math Quiz",
        "priority": "High",
        "due_date": "2026-10-10",
        "reminder_offset": "1_day_before"
    })
    assert create_res.status_code == 201
    task_id = create_res.get_json()["task"]["id"]
    assert create_res.get_json()["task"]["reminder_offset"] == "1_day_before"

    # Update
    update_res = auth_client.put(f"/api/tasks/{task_id}", json={
        "title": "Math Final Quiz",
        "priority": "Medium",
        "due_date": "2026-10-12",
        "reminder_offset": "same_day",
        "status": "Pending"
    })
    assert update_res.status_code == 200
    assert update_res.get_json()["task"]["title"] == "Math Final Quiz"

    # Toggle Complete
    comp_res = auth_client.patch(f"/api/tasks/{task_id}/complete")
    assert comp_res.status_code == 200
    assert comp_res.get_json()["task"]["status"] == "Completed"
    assert comp_res.get_json()["task"]["completed_at"] is not None

    # Delete
    del_res = auth_client.delete(f"/api/tasks/{task_id}")
    assert del_res.status_code == 200


def test_ghost_stale_session_protection(client):
    """Test that a stale or non-existent session user_id returns 401 instead of crashing with 500 foreign key failure."""
    with client.session_transaction() as sess:
        sess["user_id"] = 99999
        sess["user_name"] = "Ghost Student"

    # GET /api/tasks must safely reject with 401
    get_res = client.get("/api/tasks")
    assert get_res.status_code == 401
    assert "Session expired" in get_res.get_json()["error"]

    # POST /api/tasks must safely reject with 401 instead of 500
    post_res = client.post("/api/tasks", json={"title": "Refill water", "priority": "Low"})
    assert post_res.status_code == 401


def test_add_task_low_priority_with_reminder(auth_client):
    """Test adding a task titled 'refill water' with Low priority, due date, and '1_day_before' reminder."""
    payload = {
        "title": "refill water",
        "description": "Stay hydrated during study sessions",
        "priority": "Low",
        "due_date": "2026-09-13",
        "reminder_offset": "1_day_before",
        "status": "Pending"
    }
    response = auth_client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Task created successfully."
    assert data["task"]["title"] == "refill water"
    assert data["task"]["priority"] == "Low"
    assert data["task"]["reminder_offset"] == "1_day_before"
    assert data["task"]["due_date"] == "2026-09-13"

    # Verify task appears in list
    list_res = auth_client.get("/api/tasks")
    assert list_res.status_code == 200
    tasks = list_res.get_json()
    assert any(t["title"] == "refill water" and t["priority"] == "Low" for t in tasks)


# -----------------------------------------------------------------
# 4. Part A: Progress Tracking Analytics Tests
# -----------------------------------------------------------------

def test_progress_analytics_api(auth_client):
    """Test /api/progress calculations for streak, rates, and priority breakdown."""
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    # Create tasks: 2 completed today, 1 completed yesterday, 1 pending High, 1 pending Low
    t1 = auth_client.post("/api/tasks", json={"title": "Task 1", "priority": "High", "status": "Pending", "due_date": today_str})
    t1_id = t1.get_json()["task"]["id"]
    auth_client.patch(f"/api/tasks/{t1_id}/complete")  # completed today

    t2 = auth_client.post("/api/tasks", json={"title": "Task 2", "priority": "Low", "status": "Pending", "due_date": today_str})
    t2_id = t2.get_json()["task"]["id"]
    auth_client.patch(f"/api/tasks/{t2_id}/complete")  # completed today

    # Pending tasks
    auth_client.post("/api/tasks", json={"title": "Pending High", "priority": "High", "due_date": today_str})
    auth_client.post("/api/tasks", json={"title": "Pending Low", "priority": "Low", "due_date": today_str})

    progress_res = auth_client.get("/api/progress")
    assert progress_res.status_code == 200
    data = progress_res.get_json()

    assert data["total_tasks"] == 4
    assert data["completed_tasks"] == 2
    assert data["pending_tasks"] == 2
    assert data["completion_rate_overall"] == 50.0
    assert data["current_streak_days"] >= 1
    assert data["priority_breakdown"]["High"] == 1
    assert data["priority_breakdown"]["Low"] == 1
    assert len(data["daily_completion_history"]) == 7
    assert "🔥" in data["motivational_message"] or "🚀" in data["motivational_message"] or "🌟" in data["motivational_message"]


# -----------------------------------------------------------------
# 5. Part B: Calendar View API Tests
# -----------------------------------------------------------------

def test_calendar_api(auth_client):
    """Test /api/tasks/calendar grouping tasks by due date for a specific month/year."""
    auth_client.post("/api/tasks", json={"title": "Midterm Exam", "priority": "High", "due_date": "2026-09-15"})
    auth_client.post("/api/tasks", json={"title": "Lab Report", "priority": "Medium", "due_date": "2026-09-15"})
    auth_client.post("/api/tasks", json={"title": "Essay Draft", "priority": "Low", "due_date": "2026-09-22"})
    auth_client.post("/api/tasks", json={"title": "Next Month Project", "priority": "High", "due_date": "2026-10-05"})

    cal_res = auth_client.get("/api/tasks/calendar?month=9&year=2026")
    assert cal_res.status_code == 200
    data = cal_res.get_json()

    assert data["month"] == 9
    assert data["year"] == 2026
    assert data["month_name"] == "September"
    assert "2026-09-15" in data["days"]
    assert len(data["days"]["2026-09-15"]) == 2
    assert "2026-09-22" in data["days"]
    assert "2026-10-05" not in data["days"]


def test_calendar_api_invalid_params(auth_client):
    """Test /api/tasks/calendar rejects invalid month or year."""
    assert auth_client.get("/api/tasks/calendar?month=13&year=2026").status_code == 400
    assert auth_client.get("/api/tasks/calendar?month=abc&year=2026").status_code == 400


# -----------------------------------------------------------------
# 6. Part C: Reminders API Tests
# -----------------------------------------------------------------

def test_reminders_api(auth_client):
    """Test /api/reminders matching logic for same_day and 1_day_before."""
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    far_future_str = (now + timedelta(days=10)).strftime("%Y-%m-%d")

    # Due today with same_day reminder
    auth_client.post("/api/tasks", json={"title": "Due Today Task", "due_date": today_str, "reminder_offset": "same_day", "priority": "High"})
    # Due tomorrow with 1_day_before reminder
    auth_client.post("/api/tasks", json={"title": "Due Tomorrow Task", "due_date": tomorrow_str, "reminder_offset": "1_day_before", "priority": "Medium"})
    # Far future with no reminder
    auth_client.post("/api/tasks", json={"title": "Future Task", "due_date": far_future_str, "reminder_offset": "none", "priority": "Low"})

    reminders_res = auth_client.get("/api/reminders")
    assert reminders_res.status_code == 200
    data = reminders_res.get_json()

    assert data["count"] >= 2
    titles = [r["title"] for r in data["reminders"]]
    assert "Due Today Task" in titles
    assert "Due Tomorrow Task" in titles
    assert "Future Task" not in titles
