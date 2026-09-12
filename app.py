"""
app.py - Main Flask Application & REST API for Student Task Manager.
Features session-based user authentication, strict data isolation,
input validation, and RESTful task management endpoints.
"""

import os
import re
import time
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, close_db, init_db, DEFAULT_DB_PATH

VALID_PRIORITIES = {"Low", "Medium", "High"}
VALID_STATUSES = {"Pending", "Completed"}
MAX_TITLE_LENGTH = 150
MAX_DESCRIPTION_LENGTH = 2000
DEFAULT_ORDER_BY = "ORDER BY CASE status WHEN 'Pending' THEN 1 ELSE 2 END, due_date ASC, id DESC"
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# In-memory login attempt tracker for brute-force protection
# Format: { "email_or_ip": {"count": int, "blocked_until": float} }
LOGIN_ATTEMPTS = {}
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 60  # seconds


def is_rate_limited(identifier):
    """Checks if a given IP or email is currently locked out from login attempts."""
    now = time.time()
    record = LOGIN_ATTEMPTS.get(identifier)
    if not record:
        return False
    if record.get("blocked_until", 0) > now:
        return True
    if record.get("blocked_until", 0) <= now and record.get("count", 0) >= MAX_LOGIN_ATTEMPTS:
        # Reset expired lockout
        LOGIN_ATTEMPTS.pop(identifier, None)
        return False
    return False


def record_failed_attempt(identifier):
    """Records a failed login attempt and applies a lockout if threshold is exceeded."""
    now = time.time()
    record = LOGIN_ATTEMPTS.setdefault(identifier, {"count": 0, "blocked_until": 0})
    record["count"] += 1
    if record["count"] >= MAX_LOGIN_ATTEMPTS:
        record["blocked_until"] = now + LOCKOUT_DURATION


def reset_login_attempts(identifier):
    """Clears failed login attempts upon successful authentication."""
    LOGIN_ATTEMPTS.pop(identifier, None)


def login_required(f):
    """
    Decorator that enforces user authentication.
    For API endpoints (under /api/), returns a 401 JSON error.
    For HTML view endpoints, redirects unauthenticated users to the /login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized. Please log in to access this resource."}), 401
            return redirect(url_for("login_view"))
        return f(*args, **kwargs)
    return decorated_function


def row_to_dict(row):
    """Converts an sqlite3.Row object into a serializable Python dictionary."""
    if row is None:
        return None
    return {
        "id": row["id"],
        "user_id": row["user_id"] if "user_id" in row.keys() else None,
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
    Configures database, session security, and registers routes.
    """
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # Configuration
    app.config.from_mapping(
        DATABASE=os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH),
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key-student-task-manager-secure-session"),
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
                    if os.environ.get("AUTO_SEED", "1") == "1":
                        from seed import seed_database
                        seed_database(db_path)
        except Exception as e:
            print(f"Notice during startup database initialization: {e}")

    def db_conn():
        return get_db(app.config["DATABASE"])

    # -------------------------------------------------------------
    # Authentication & Page Views
    # -------------------------------------------------------------
    @app.route("/")
    @login_required
    def index():
        """Serves the main student dashboard for authenticated users."""
        return render_template(
            "index.html",
            user_name=session.get("user_name", "Student"),
            user_email=session.get("user_email", "")
        )

    @app.route("/login", methods=["GET", "POST"])
    def login_view():
        """Handles student login via HTML form submission or JSON API."""
        if request.method == "GET":
            if "user_id" in session:
                return redirect(url_for("index"))
            return render_template("login.html")

        # Process POST Login
        is_json = request.is_json
        data = request.get_json(silent=True) if is_json else request.form

        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        client_identifier = f"{request.remote_addr}_{email}"

        if not email or not password:
            error_msg = "Please provide both email and password."
            if is_json:
                return jsonify({"error": error_msg}), 400
            return render_template("login.html", error=error_msg, email=email), 400

        if is_rate_limited(client_identifier):
            error_msg = f"Too many failed login attempts. Please wait {LOCKOUT_DURATION} seconds."
            if is_json:
                return jsonify({"error": error_msg}), 429
            return render_template("login.html", error=error_msg, email=email), 429

        db = db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT id, name, email, password_hash FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            record_failed_attempt(client_identifier)
            error_msg = "Invalid email or password. Please try again."
            if is_json:
                return jsonify({"error": error_msg}), 401
            return render_template("login.html", error=error_msg, email=email), 401

        # Authentication success
        reset_login_attempts(client_identifier)
        session.clear()
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]

        if is_json:
            return jsonify({
                "message": "Login successful.",
                "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
            }), 200

        return redirect(url_for("index"))

    @app.route("/signup", methods=["GET", "POST"])
    def signup_view():
        """Handles student registration."""
        if request.method == "GET":
            if "user_id" in session:
                return redirect(url_for("index"))
            return render_template("signup.html")

        # Process POST Signup
        is_json = request.is_json
        data = request.get_json(silent=True) if is_json else request.form

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        confirm_password = data.get("confirm_password") or ""

        # Validation
        if not name:
            error_msg = "Your full name is required."
            if is_json:
                return jsonify({"error": error_msg}), 400
            return render_template("signup.html", error=error_msg, name=name, email=email), 400

        if not email or not EMAIL_REGEX.match(email):
            error_msg = "Please enter a valid email address."
            if is_json:
                return jsonify({"error": error_msg}), 400
            return render_template("signup.html", error=error_msg, name=name, email=email), 400

        if len(password) < 8:
            error_msg = "Password must be at least 8 characters long."
            if is_json:
                return jsonify({"error": error_msg}), 400
            return render_template("signup.html", error=error_msg, name=name, email=email), 400

        if password != confirm_password:
            error_msg = "Passwords do not match."
            if is_json:
                return jsonify({"error": error_msg}), 400
            return render_template("signup.html", error=error_msg, name=name, email=email), 400

        db = db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone() is not None:
            error_msg = "An account with this email already exists."
            if is_json:
                return jsonify({"error": error_msg}), 400
            return render_template("signup.html", error=error_msg, name=name, email=email), 400

        # Hash password and store user
        pw_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, pw_hash)
        )
        db.commit()
        user_id = cursor.lastrowid

        # Auto-login after successful registration
        session.clear()
        session["user_id"] = user_id
        session["user_name"] = name
        session["user_email"] = email

        if is_json:
            return jsonify({
                "message": "Account created successfully.",
                "user": {"id": user_id, "name": name, "email": email}
            }), 201

        return redirect(url_for("index"))

    @app.route("/logout", methods=["GET", "POST"])
    def logout():
        """Logs out the active student session."""
        session.clear()
        if request.is_json:
            return jsonify({"message": "Logged out successfully."}), 200
        return redirect(url_for("login_view"))

    @app.route("/api/me", methods=["GET"])
    @login_required
    def current_user_api():
        """Returns details of the currently authenticated student."""
        return jsonify({
            "id": session.get("user_id"),
            "name": session.get("user_name"),
            "email": session.get("user_email")
        }), 200

    # -------------------------------------------------------------
    # REST API Routes (Protected & User-Isolated)
    # -------------------------------------------------------------
    @app.route("/api/tasks", methods=["GET"])
    @login_required
    def list_tasks():
        """
        List tasks belonging strictly to the authenticated student.
        Supports optional query parameter filters:
          - ?status=Pending or ?status=Completed
          - ?priority=Low, Medium, or High
        """
        user_id = session["user_id"]
        status_filter = request.args.get("status")
        priority_filter = request.args.get("priority")

        query = "SELECT * FROM tasks WHERE user_id = ?"
        params = [user_id]

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
    @login_required
    def get_task(task_id):
        """Retrieve details of a single task owned by the authenticated student."""
        user_id = session["user_id"]
        db = db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        row = cursor.fetchone()

        if row is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

        return jsonify(row_to_dict(row)), 200

    @app.route("/api/tasks", methods=["POST"])
    @login_required
    def create_task():
        """
        Create a new student task linked to the authenticated student.
        Request JSON:
          - title (required, non-empty, max 150 chars)
          - description (optional, max 2000 chars)
          - priority (optional, default 'Medium')
          - due_date (optional, YYYY-MM-DD)
        """
        user_id = session["user_id"]
        data = request.get_json(silent=True)
        cleaned, error = validate_and_parse_task_payload(data, is_update=False)
        if error:
            return jsonify({"error": error}), 400

        db = db_conn()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (user_id, title, description, priority, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, cleaned["title"], cleaned["description"], cleaned["priority"], cleaned["due_date"], cleaned["status"])
        )
        db.commit()
        new_id = cursor.lastrowid

        cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (new_id, user_id))
        new_task = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": "Task created successfully.",
            "task": new_task
        }), 201

    @app.route("/api/tasks/<int:task_id>", methods=["PUT"])
    @login_required
    def update_task(task_id):
        """
        Update an existing task owned by the authenticated student.
        """
        user_id = session["user_id"]
        db = db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
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
            WHERE id = ? AND user_id = ?
            """,
            (cleaned["title"], cleaned["description"], cleaned["priority"], cleaned["due_date"], cleaned["status"], task_id, user_id)
        )
        db.commit()

        cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        updated_task = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": "Task updated successfully.",
            "task": updated_task
        }), 200

    @app.route("/api/tasks/<int:task_id>/complete", methods=["PATCH"])
    @login_required
    def toggle_complete_task(task_id):
        """
        Mark a task complete or pending for the authenticated student.
        """
        user_id = session["user_id"]
        db = db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
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
            new_status = "Completed" if existing["status"] == "Pending" else "Pending"

        cursor.execute("UPDATE tasks SET status = ? WHERE id = ? AND user_id = ?", (new_status, task_id, user_id))
        db.commit()

        cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        updated_task = row_to_dict(cursor.fetchone())

        return jsonify({
            "message": f"Task marked as {new_status}.",
            "task": updated_task
        }), 200

    @app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
    @login_required
    def delete_task(task_id):
        """Delete a task owned by the authenticated student."""
        user_id = session["user_id"]
        db = db_conn()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        existing = cursor.fetchone()
        if existing is None:
            return jsonify({"error": f"Task with ID {task_id} not found."}), 404

        cursor.execute("DELETE FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        db.commit()

        return jsonify({"message": f"Task {task_id} deleted successfully."}), 200

    @app.route("/api/tasks/search", methods=["GET"])
    @login_required
    def search_tasks():
        """
        Search tasks by title or description owned by the authenticated student.
        """
        user_id = session["user_id"]
        query_param = request.args.get("q", "").strip()
        db = db_conn()
        cursor = db.cursor()

        if not query_param:
            cursor.execute(f"SELECT * FROM tasks WHERE user_id = ? {DEFAULT_ORDER_BY}", (user_id,))
        else:
            search_pattern = f"%{query_param}%"
            cursor.execute(
                f"""
                SELECT * FROM tasks
                WHERE user_id = ? AND (title LIKE ? OR description LIKE ?)
                {DEFAULT_ORDER_BY}
                """,
                (user_id, search_pattern, search_pattern)
            )

        rows = cursor.fetchall()
        tasks = [row_to_dict(r) for r in rows]
        return jsonify(tasks), 200

    return app


# Default app instance
app = create_app()

if __name__ == "__main__":
    if not os.path.exists(DEFAULT_DB_PATH):
        init_db()
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
    print(f"Starting Student Task Manager server (debug={debug_mode}) on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=debug_mode)
