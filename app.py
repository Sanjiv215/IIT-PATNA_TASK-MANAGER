"""
app.py - Main Flask Application & REST API for Student Task Manager.
Provides endpoints for CRUD operations, searching, filtering, and serving the frontend.
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from database import get_db, close_db, init_db, DEFAULT_DB_PATH

VALID_PRIORITIES = {"Low", "Medium", "High"}
VALID_STATUSES = {"Pending", "Completed"}
MAX_TITLE_LENGTH = 150
MAX_DESCRIPTION_LENGTH = 2000
DEFAULT_ORDER_BY = "ORDER BY CASE status WHEN 'Pending' THEN 1 ELSE 2 END, due_date ASC, id DESC"


def row_to_dict(row):
    """Converts an sqlite3.Row object into a serializable Python dictionary."""
    if row is None:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "priority": row["priority"],
        "due_date": row["due_date"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


def validate_and_parse_task_payload(data, is_update=False, existing=None):
    """
    Validates and cleans input JSON payload for creating or updating a task.
    Returns (cleaned_data, error_message). If invalid, cleaned_data is None.
    """
    if not isinstance(data, dict):
        return None, "Invalid or missing JSON payload."

    # 1. Title validation
    if "title" in data or not is_update:
        raw_title = data.get("title")
        if not isinstance(raw_title, str) or not raw_title.strip():
            return None, "Task title is required and cannot be empty."
        title = raw_title.strip()
        if len(title) > MAX_TITLE_LENGTH:
            return None, f"Task title exceeds maximum allowed length of {MAX_TITLE_LENGTH} characters."
    else:
        title = existing["title"]

    # 2. Description validation
    if "description" in data:
        raw_desc = data.get("description")
        description = str(raw_desc).strip() if raw_desc is not None else ""
        if len(description) > MAX_DESCRIPTION_LENGTH:
            return None, f"Description exceeds maximum allowed length of {MAX_DESCRIPTION_LENGTH} characters."
    else:
        description = existing["description"] if is_update and existing else ""

    # 3. Priority validation
    if "priority" in data:
        priority = data.get("priority")
        if priority not in VALID_PRIORITIES:
            return None, f"Invalid priority '{priority}'. Allowed: {sorted(list(VALID_PRIORITIES))}"
    else:
        priority = existing["priority"] if is_update and existing else "Medium"

    # 4. Status validation
    if "status" in data:
        status = data.get("status")
        if status not in VALID_STATUSES:
            return None, f"Invalid status '{status}'. Allowed: {sorted(list(VALID_STATUSES))}"
    else:
        status = existing["status"] if is_update and existing else "Pending"

    # 5. Due Date validation
    if "due_date" in data:
        raw_due_date = data.get("due_date")
        if raw_due_date is not None and str(raw_due_date).strip() != "":
            due_date_str = str(raw_due_date).strip()
            try:
                datetime.strptime(due_date_str, "%Y-%m-%d")
                due_date = due_date_str
            except ValueError:
                return None, f"Invalid due_date format '{due_date_str}'. Expected 'YYYY-MM-DD'."
        else:
            due_date = None
    else:
        due_date = existing["due_date"] if is_update and existing else None

    cleaned = {
        "title": title,
        "description": description,
        "priority": priority,
        "due_date": due_date,
        "status": status,
    }
    return cleaned, None


def create_app(test_config=None):
    """
    Application factory pattern.
    Allows easy configuration for production and testing environments.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Configuration
    app.config.from_mapping(
        DATABASE=os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH),
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-student-task-manager"),
    )

    if test_config is not None:
        app.config.update(test_config)

    # Register teardown function to clean up database connections
    app.teardown_appcontext(close_db)

    # Auto-initialize database on startup if database file or tables don't exist yet
    db_path = app.config["DATABASE"]
    if test_config is None and db_path != ":memory:":
        try:
            if not os.path.exists(db_path):
                with app.app_context():
                    init_db(db_path)
                    # Automatically seed sample tasks on initial production deployment
                    if os.environ.get("AUTO_SEED", "1") == "1":
                        from seed import seed_database
                        seed_database(db_path)
        except Exception as e:
            print(f"Notice during startup database initialization: {e}")

    def db_conn():
        return get_db(app.config["DATABASE"])

    # -------------------------------------------------------------
    # Frontend Route
    # -------------------------------------------------------------
    @app.route("/")
    def index():
        """Serves the main dashboard user interface."""
        return render_template("index.html")

    # -------------------------------------------------------------
    # REST API Routes
    # -------------------------------------------------------------
    @app.route("/api/tasks", methods=["GET"])
    def list_tasks():
        """
        List all tasks.
        Supports optional query parameter filters:
          - ?status=Pending or ?status=Completed
          - ?priority=Low, Medium, or High
        """
        status_filter = request.args.get("status")
        priority_filter = request.args.get("priority")

        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        if status_filter:
            if status_filter not in VALID_STATUSES:
                return jsonify({"error": f"Invalid status filter. Allowed: {sorted(list(VALID_STATUSES))}"}), 400
            query += " AND status = ?"
            params.append(status_filter)

        if priority_filter:
            if priority_filter not in VALID_PRIORITIES:
                return jsonify({"error": f"Invalid priority filter. Allowed: {sorted(list(VALID_PRIORITIES))}"}), 400
            query += " AND priority = ?"
            params.append(priority_filter)

        query += f" {DEFAULT_ORDER_BY}"

        db = db_conn()
        cursor = db.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

        tasks = [row_to_dict(r) for r in rows]
        return jsonify(tasks), 200

    @app.route("/api/tasks/<int:task_id>", methods=["GET"])
    def get_task(task_id):
        """Retrieve details of a single task by ID."""
        db = db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        if row is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

        return jsonify(row_to_dict(row)), 200

    @app.route("/api/tasks", methods=["POST"])
    def create_task():
        """
        Create a new student task.
        Request JSON:
          - title (required, non-empty, max 150 chars)
          - description (optional, max 2000 chars)
          - priority (optional, default 'Medium')
          - due_date (optional, YYYY-MM-DD)
        """
        data = request.get_json(silent=True)
        cleaned, error = validate_and_parse_task_payload(data, is_update=False)
        if error:
            return jsonify({"error": error}), 400

        db = db_conn()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (title, description, priority, due_date, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (cleaned["title"], cleaned["description"], cleaned["priority"], cleaned["due_date"], cleaned["status"])
        )
        db.commit()
        new_id = cursor.lastrowid

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (new_id,))
        new_task = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": "Task created successfully.",
            "task": new_task
        }), 201

    @app.route("/api/tasks/<int:task_id>", methods=["PUT"])
    def update_task(task_id):
        """
        Update an existing task's information.
        Request JSON:
          - title (required, non-empty)
          - description (optional)
          - priority (required: Low, Medium, High)
          - due_date (optional, YYYY-MM-DD)
          - status (optional: Pending, Completed)
        """
        db = db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if existing is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

        data = request.get_json(silent=True)
        cleaned, error = validate_and_parse_task_payload(data, is_update=True, existing=existing)
        if error:
            return jsonify({"error": error}), 400

        cursor.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, priority = ?, due_date = ?, status = ?
            WHERE id = ?
            """,
            (cleaned["title"], cleaned["description"], cleaned["priority"], cleaned["due_date"], cleaned["status"], task_id)
        )
        db.commit()

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        updated_task = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": "Task updated successfully.",
            "task": updated_task
        }), 200

    @app.route("/api/tasks/<int:task_id>/complete", methods=["PATCH"])
    def toggle_complete_task(task_id):
        """
        Mark a task complete or pending.
        Accepts optional JSON {"completed": true/false}.
        If not specified in JSON, toggles the current state.
        """
        db = db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if existing is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

        data = request.get_json(silent=True) or {}
        if "completed" in data:
            new_status = "Completed" if data["completed"] else "Pending"
        elif "status" in data:
            if data["status"] not in VALID_STATUSES:
                return jsonify({"error": f"Invalid status '{data['status']}'."}), 400
            new_status = data["status"]
        else:
            # Toggle current status
            new_status = "Completed" if existing["status"] == "Pending" else "Pending"

        cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
        db.commit()

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        updated_task = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": f"Task marked as {new_status}.",
            "task": updated_task
        }), 200

    @app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
    def delete_task(task_id):
        """Delete a task by ID."""
        db = db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        existing = cursor.fetchone()
        if existing is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()

        return jsonify({"message": f"Task {task_id} deleted successfully."}), 200

    @app.route("/api/tasks/search", methods=["GET"])
    def search_tasks():
        """
        Search tasks by title or description matching query string `q`.
        GET /api/tasks/search?q=calculus
        """
        query_param = request.args.get("q", "").strip()
        db = db_conn()
        cursor = db.cursor()

        if not query_param:
            # If search string is empty, return all tasks
            cursor.execute(f"SELECT * FROM tasks {DEFAULT_ORDER_BY}")
        else:
            search_pattern = f"%{query_param}%"
            cursor.execute(
                f"""
                SELECT * FROM tasks
                WHERE title LIKE ? OR description LIKE ?
                {DEFAULT_ORDER_BY}
                """,
                (search_pattern, search_pattern)
            )

        rows = cursor.fetchall()
        tasks = [row_to_dict(r) for r in rows]
        return jsonify(tasks), 200

    return app


# Default app instance for running via gunicorn or flask run
app = create_app()

if __name__ == "__main__":
    if not os.path.exists(DEFAULT_DB_PATH):
        init_db()
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
    print(f"Starting Student Task Manager server (debug={debug_mode}) on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
