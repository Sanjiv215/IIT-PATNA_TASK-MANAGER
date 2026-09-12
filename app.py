"""
app.py - Main Flask Application & REST API for Student Task Manager.
Provides endpoints for CRUD operations, searching, filtering, and serving the frontend.
"""

import os
from flask import Flask, render_template, request, jsonify, abort
from database import get_db, close_db, init_db, DEFAULT_DB_PATH

VALID_PRIORITIES = {"Low", "Medium", "High"}
VALID_STATUSES = {"Pending", "Completed"}


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


def create_app(test_config=None):
    """
    Application factory pattern.
    Allows easy configuration for production and testing environments.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Default configuration
    app.config.from_mapping(
        DATABASE=DEFAULT_DB_PATH,
        SECRET_KEY="dev-secret-key-student-task-manager",
    )

    if test_config is not None:
        app.config.update(test_config)

    # Register teardown function to clean up database connections
    app.teardown_appcontext(close_db)

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
                return jsonify({"error": f"Invalid status filter. Allowed: {list(VALID_STATUSES)}"}), 400
            query += " AND status = ?"
            params.append(status_filter)

        if priority_filter:
            if priority_filter not in VALID_PRIORITIES:
                return jsonify({"error": f"Invalid priority filter. Allowed: {list(VALID_PRIORITIES)}"}), 400
            query += " AND priority = ?"
            params.append(priority_filter)

        query += " ORDER BY CASE status WHEN 'Pending' THEN 1 ELSE 2 END, due_date ASC, id DESC"

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
          - title (required, non-empty)
          - description (optional)
          - priority (optional, default 'Medium')
          - due_date (optional, YYYY-MM-DD)
        """
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid or missing JSON payload."}), 400

        title = data.get("title", "").strip() if isinstance(data.get("title"), str) else ""
        if not title:
            return jsonify({"error": "Task title is required and cannot be empty."}), 400

        description = data.get("description", "").strip() if isinstance(data.get("description"), str) else ""
        priority = data.get("priority", "Medium")
        if priority not in VALID_PRIORITIES:
            return jsonify({"error": f"Invalid priority '{priority}'. Allowed: {sorted(list(VALID_PRIORITIES))}"}), 400

        due_date = data.get("due_date")
        if due_date is not None:
            due_date = str(due_date).strip()
            if due_date == "":
                due_date = None

        status = data.get("status", "Pending")
        if status not in VALID_STATUSES:
            return jsonify({"error": f"Invalid status '{status}'. Allowed: {sorted(list(VALID_STATUSES))}"}), 400

        db = db_conn()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (title, description, priority, due_date, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, description, priority, due_date, status)
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
        if not data:
            return jsonify({"error": "Invalid or missing JSON payload."}), 400

        title = data.get("title", "").strip() if isinstance(data.get("title"), str) else ""
        if not title:
            return jsonify({"error": "Task title cannot be empty."}), 400

        description = data.get("description", "").strip() if isinstance(data.get("description"), str) else ""
        
        priority = data.get("priority", existing["priority"])
        if priority not in VALID_PRIORITIES:
            return jsonify({"error": f"Invalid priority '{priority}'. Allowed: {sorted(list(VALID_PRIORITIES))}"}), 400

        status = data.get("status", existing["status"])
        if status not in VALID_STATUSES:
            return jsonify({"error": f"Invalid status '{status}'. Allowed: {sorted(list(VALID_STATUSES))}"}), 400

        due_date = data.get("due_date", existing["due_date"])
        if due_date is not None:
            due_date = str(due_date).strip()
            if due_date == "":
                due_date = None

        cursor.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, priority = ?, due_date = ?, status = ?
            WHERE id = ?
            """,
            (title, description, priority, due_date, status, task_id)
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
            cursor.execute("SELECT * FROM tasks ORDER BY CASE status WHEN 'Pending' THEN 1 ELSE 2 END, due_date ASC, id DESC")
        else:
            search_pattern = f"%{query_param}%"
            cursor.execute(
                """
                SELECT * FROM tasks
                WHERE title LIKE ? OR description LIKE ?
                ORDER BY CASE status WHEN 'Pending' THEN 1 ELSE 2 END, due_date ASC, id DESC
                """,
                (search_pattern, search_pattern)
            )

        rows = cursor.fetchall()
        tasks = [row_to_dict(r) for r in rows]
        return jsonify(tasks), 200

    return app


# Default app instance for running via python app.py or flask run
app = create_app()

if __name__ == "__main__":
    # Ensure database is initialized before serving
    if not os.path.exists(DEFAULT_DB_PATH):
        init_db()
    print("Starting Student Task Manager server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
