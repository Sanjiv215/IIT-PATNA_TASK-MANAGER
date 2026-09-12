"""
Unit and integration tests for Student Task Manager REST API routes.
"""

import json


def test_index_page(client):
    """Test that the homepage HTML renders successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Task Manager" in response.data


def test_create_task_success(client):
    """Test creating a new task with complete valid information."""
    payload = {
        "title": "Math Assignment 1",
        "description": "Solve problems 1 to 10 on page 45",
        "priority": "High",
        "due_date": "2026-09-30",
        "status": "Pending"
    }
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    data = response.get_json()
    assert "task" in data
    assert data["task"]["title"] == "Math Assignment 1"
    assert data["task"]["priority"] == "High"
    assert data["task"]["status"] == "Pending"
    assert data["task"]["id"] is not None


def test_create_task_validation_missing_title(client):
    """Test validation failure when title is missing or empty."""
    response = client.post("/api/tasks", json={"title": "", "priority": "Low"})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_create_task_validation_invalid_priority(client):
    """Test validation failure when priority is not Low/Medium/High."""
    response = client.post("/api/tasks", json={"title": "Test Task", "priority": "Urgent"})
    assert response.status_code == 400


def test_create_task_validation_invalid_due_date(client):
    """Test validation failure when due_date format is malformed."""
    response = client.post("/api/tasks", json={"title": "Test Task", "due_date": "not-a-date"})
    assert response.status_code == 400
    assert "Invalid due_date format" in response.get_json()["error"]


def test_create_task_validation_oversized_title(client):
    """Test validation failure when title exceeds 150 characters."""
    oversized_title = "A" * 151
    response = client.post("/api/tasks", json={"title": oversized_title})
    assert response.status_code == 400
    assert "exceeds maximum allowed length" in response.get_json()["error"]


def test_get_single_task(client):
    """Test retrieving a single task by ID."""
    create_res = client.post("/api/tasks", json={"title": "Read Chapter 4", "priority": "Medium"})
    task_id = create_res.get_json()["task"]["id"]

    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 200
    task = get_res.get_json()
    assert task["id"] == task_id
    assert task["title"] == "Read Chapter 4"


def test_get_task_not_found(client):
    """Test 404 response for non-existent task ID."""
    response = client.get("/api/tasks/99999")
    assert response.status_code == 404


def test_list_all_tasks(client):
    """Test listing all tasks."""
    client.post("/api/tasks", json={"title": "Task A", "priority": "Low"})
    client.post("/api/tasks", json={"title": "Task B", "priority": "High"})

    response = client.get("/api/tasks")
    assert response.status_code == 200
    tasks = response.get_json()
    assert len(tasks) >= 2
    titles = [t["title"] for t in tasks]
    assert "Task A" in titles
    assert "Task B" in titles


def test_update_task(client):
    """Test updating task title, priority, and description."""
    create_res = client.post("/api/tasks", json={"title": "Draft Presentation", "priority": "Medium"})
    task_id = create_res.get_json()["task"]["id"]

    update_payload = {
        "title": "Finalize Presentation Slides",
        "description": "Added 10 slides and citations",
        "priority": "High",
        "due_date": "2026-10-01",
        "status": "Pending"
    }
    update_res = client.put(f"/api/tasks/{task_id}", json=update_payload)
    assert update_res.status_code == 200
    updated = update_res.get_json()["task"]
    assert updated["title"] == "Finalize Presentation Slides"
    assert updated["priority"] == "High"
    assert updated["description"] == "Added 10 slides and citations"


def test_update_task_invalid_payload(client):
    """Test updating task with invalid priority."""
    create_res = client.post("/api/tasks", json={"title": "Presentation", "priority": "Medium"})
    task_id = create_res.get_json()["task"]["id"]

    res = client.put(f"/api/tasks/{task_id}", json={"priority": "Critical"})
    assert res.status_code == 400


def test_toggle_complete_task(client):
    """Test toggling task completion status via PATCH."""
    create_res = client.post("/api/tasks", json={"title": "Chemistry Quiz Revision", "priority": "Medium"})
    task_id = create_res.get_json()["task"]["id"]

    # 1. Toggle to Completed
    patch_res1 = client.patch(f"/api/tasks/{task_id}/complete")
    assert patch_res1.status_code == 200
    assert patch_res1.get_json()["task"]["status"] == "Completed"

    # 2. Toggle back to Pending
    patch_res2 = client.patch(f"/api/tasks/{task_id}/complete")
    assert patch_res2.status_code == 200
    assert patch_res2.get_json()["task"]["status"] == "Pending"

    # 3. Explicit set via JSON
    patch_res3 = client.patch(f"/api/tasks/{task_id}/complete", json={"completed": True})
    assert patch_res3.status_code == 200
    assert patch_res3.get_json()["task"]["status"] == "Completed"


def test_delete_task(client):
    """Test deleting a task."""
    create_res = client.post("/api/tasks", json={"title": "Temporary Task", "priority": "Low"})
    task_id = create_res.get_json()["task"]["id"]

    del_res = client.delete(f"/api/tasks/{task_id}")
    assert del_res.status_code == 200

    # Ensure task no longer exists
    get_res = client.get(f"/api/tasks/{task_id}")
    assert get_res.status_code == 404


def test_filter_tasks_by_status(client):
    """Test filtering tasks by status query param."""
    client.post("/api/tasks", json={"title": "Pending Task 1", "status": "Pending"})
    client.post("/api/tasks", json={"title": "Completed Task 1", "status": "Completed"})

    res_pending = client.get("/api/tasks?status=Pending")
    assert res_pending.status_code == 200
    pending_tasks = res_pending.get_json()
    assert all(t["status"] == "Pending" for t in pending_tasks)

    res_completed = client.get("/api/tasks?status=Completed")
    assert res_completed.status_code == 200
    completed_tasks = res_completed.get_json()
    assert all(t["status"] == "Completed" for t in completed_tasks)


def test_filter_tasks_by_priority(client):
    """Test filtering tasks by priority query param."""
    client.post("/api/tasks", json={"title": "Low Priority Task", "priority": "Low"})
    client.post("/api/tasks", json={"title": "High Priority Task", "priority": "High"})

    res_high = client.get("/api/tasks?priority=High")
    assert res_high.status_code == 200
    high_tasks = res_high.get_json()
    assert all(t["priority"] == "High" for t in high_tasks)
    assert any(t["title"] == "High Priority Task" for t in high_tasks)


def test_search_tasks_by_title_and_description(client):
    """Test search endpoint with keyword query."""
    client.post("/api/tasks", json={"title": "Biology Lab Experiment", "description": "Microscope cell staining"})
    client.post("/api/tasks", json={"title": "Literature Reading", "description": "Read poetry section"})

    # Search title
    res1 = client.get("/api/tasks/search?q=Biology")
    assert res1.status_code == 200
    results1 = res1.get_json()
    assert len(results1) >= 1
    assert any("Biology" in t["title"] for t in results1)

    # Search description
    res2 = client.get("/api/tasks/search?q=staining")
    assert res2.status_code == 200
    results2 = res2.get_json()
    assert len(results2) >= 1
    assert any("Biology" in t["title"] for t in results2)
