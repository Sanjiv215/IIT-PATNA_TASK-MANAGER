"""
app.py - Main Flask Application & REST API for Student Task Manager.
Features session-based user authentication, task management,
personalized progress analytics, calendar view API, reminder system,
and comprehensive error handling.
"""

import os
import re
import time
import logging
import traceback
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db, close_db, init_db, DEFAULT_DB_PATH

VALID_PRIORITIES = {"Low", "Medium", "High"}
VALID_STATUSES = {"Pending", "Completed"}
VALID_REMINDERS = {"none", "same_day", "1_day_before", "2_days_before"}
MAX_TITLE_LENGTH = 150
MAX_DESCRIPTION_LENGTH = 2000
DEFAULT_ORDER_BY = "ORDER BY CASE status WHEN 'Pending' THEN 1 ELSE 2 END, due_date ASC, id DESC"
EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# In-memory login attempt tracker for brute-force protection
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
    Verifies that the session user_id exists in the users table.
    For API endpoints (under /api/), returns 401 JSON.
    For HTML views, redirects to /login.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Unauthorized. Please log in to access this resource."}), 401
            return redirect(url_for("login_view"))

        # Verify that the user still exists in the database
        db_path = current_app.config.get("DATABASE", DEFAULT_DB_PATH)
        db = get_db(db_path)
        cursor = db.cursor()
        cursor.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()

        if user_row is None:
            session.clear()
            if request.path.startswith("/api/") or request.is_json:
                return jsonify({"error": "Session expired or user not found. Please log in again."}), 401
            return redirect(url_for("login_view"))

        return f(*args, **kwargs)
    return decorated_function


def row_to_dict(row):
    """Converts an sqlite3.Row object into a serializable Python dictionary."""
    if row is None:
        return None
    keys = row.keys()
    return {
        "id": row["id"],
        "user_id": row["user_id"] if "user_id" in keys else None,
        "title": row["title"],
        "description": row["description"],
        "priority": row["priority"],
        "due_date": row["due_date"] if row["due_date"] else None,
        "status": row["status"],
        "reminder_offset": row["reminder_offset"] if "reminder_offset" in keys else "none",
        "completed_at": row["completed_at"] if "completed_at" in keys else None,
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

    # 6. Reminder Offset validation
    if "reminder_offset" in data:
        reminder_offset = data.get("reminder_offset", "none")
        if reminder_offset not in VALID_REMINDERS:
            return None, f"Invalid reminder_offset '{reminder_offset}'. Allowed: {sorted(list(VALID_REMINDERS))}"
    else:
        reminder_offset = existing["reminder_offset"] if is_update and existing and "reminder_offset" in existing.keys() else "none"

    cleaned = {
        "title": title,
        "description": description,
        "priority": priority,
        "due_date": due_date,
        "status": status,
        "reminder_offset": reminder_offset
    }
    return cleaned, None


def create_app(test_config=None):
    """
    Application factory pattern.
    Configures database, session security, error handlers, and registers routes.
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
            app.logger.warning(f"Notice during startup database initialization: {e}")

    def db_conn():
        return get_db(app.config["DATABASE"])

    # -------------------------------------------------------------
    # Global Error Handlers (500, 404, 400)
    # -------------------------------------------------------------
    @app.errorhandler(500)
    def handle_internal_server_error(e):
        """Friendly error handler for 500 Internal Server Errors."""
        app.logger.error(f"Internal Server Error: {e}\n{traceback.format_exc()}")
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "An internal server error occurred. Please try again later."}), 500
        return render_template("login.html", error="An internal server error occurred. Please refresh or try again."), 500

    @app.errorhandler(404)
    def handle_not_found_error(e):
        """Friendly error handler for 404 Not Found."""
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found."}), 404
        return redirect(url_for("index"))

    @app.errorhandler(Exception)
    def handle_unhandled_exception(e):
        """Catches unhandled exceptions, logs traceback, and returns a safe response."""
        app.logger.error(f"Unhandled Exception on {request.path} [{request.method}]: {e}\n{traceback.format_exc()}")
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({"error": "An unexpected error occurred. Please try again."}), 500
        return render_template("login.html", error="An unexpected error occurred. Please try again."), 500

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

        is_json = request.is_json
        data = request.get_json(silent=True) if is_json else request.form

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        confirm_password = data.get("confirm_password") or ""

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

        pw_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, pw_hash)
        )
        db.commit()
        user_id = cursor.lastrowid

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
        Supports query params ?status= and ?priority=
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
        Create a new student task.
        """
        user_id = session["user_id"]
        data = request.get_json(silent=True)
        cleaned, error = validate_and_parse_task_payload(data, is_update=False)
        if error:
            return jsonify({"error": error}), 400

        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if cleaned["status"] == "Completed" else None

        db = db_conn()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (user_id, title, description, priority, due_date, status, reminder_offset, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, cleaned["title"], cleaned["description"], cleaned["priority"], cleaned["due_date"], cleaned["status"], cleaned["reminder_offset"], completed_at)
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
        """Update an existing task owned by the authenticated student."""
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

        if cleaned["status"] == "Completed" and existing["status"] != "Completed":
            completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif cleaned["status"] == "Pending":
            completed_at = None
        else:
            completed_at = existing["completed_at"] if "completed_at" in existing.keys() else None

        cursor.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, priority = ?, due_date = ?, status = ?, reminder_offset = ?, completed_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (cleaned["title"], cleaned["description"], cleaned["priority"], cleaned["due_date"], cleaned["status"], cleaned["reminder_offset"], completed_at, task_id, user_id)
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
        """Mark a task complete or pending for the authenticated student."""
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

        completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if new_status == "Completed" else None

        cursor.execute("UPDATE tasks SET status = ?, completed_at = ? WHERE id = ? AND user_id = ?", (new_status, completed_at, task_id, user_id))
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

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()

        return jsonify({"message": f"Task {task_id} deleted successfully."}), 200

    @app.route("/api/tasks/search", methods=["GET"])
    @login_required
    def search_tasks():
        """Search tasks by title or description owned by the authenticated student."""
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

    # -------------------------------------------------------------
    # Part A: Personalized Progress Analytics API
    # -------------------------------------------------------------
    @app.route("/api/progress", methods=["GET"])
    @login_required
    def get_progress():
        """
        Returns personalized learning and completion metrics for the student.
        Robustly handles missing due dates, empty strings, and null timestamps.
        """
        user_id = session["user_id"]
        db = db_conn()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        tasks = [row_to_dict(r) for r in rows]

        now = datetime.now()
        today_date_str = now.strftime("%Y-%m-%d")

        total = len(tasks)
        completed = sum(1 for t in tasks if t["status"] == "Completed")
        pending = total - completed

        # Safe overdue check (must have valid non-empty due_date string)
        overdue = 0
        for t in tasks:
            if t["status"] == "Pending" and t.get("due_date") and str(t["due_date"]).strip():
                due_val = str(t["due_date"]).strip()
                if len(due_val) == 10 and due_val < today_date_str:
                    overdue += 1

        # Overall completion rate
        completion_rate_overall = round((completed / total * 100), 1) if total > 0 else 0.0

        # Current week metrics (Monday to Sunday)
        start_of_week = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
        week_tasks = [t for t in tasks if t.get("due_date") and str(t["due_date"]).strip() >= start_of_week]
        week_completed = sum(1 for t in week_tasks if t["status"] == "Completed")
        completion_rate_week = round((week_completed / len(week_tasks) * 100), 1) if len(week_tasks) > 0 else completion_rate_overall

        # Pending breakdown by priority
        priority_breakdown = {
            "High": sum(1 for t in tasks if t["status"] == "Pending" and t["priority"] == "High"),
            "Medium": sum(1 for t in tasks if t["status"] == "Pending" and t["priority"] == "Medium"),
            "Low": sum(1 for t in tasks if t["status"] == "Pending" and t["priority"] == "Low")
        }

        # 7-Day Completion History (Last 7 days)
        daily_history = []
        completed_date_set = set()
        for i in range(6, -1, -1):
            day_dt = now - timedelta(days=i)
            day_str = day_dt.strftime("%Y-%m-%d")
            day_count = sum(1 for t in tasks if t.get("completed_at") and str(t["completed_at"]).startswith(day_str))
            daily_history.append({"date": day_str, "day_name": day_dt.strftime("%a"), "count": day_count})
            if day_count > 0:
                completed_date_set.add(day_str)

        # Streak calculation: Consecutive days ending today or yesterday
        streak = 0
        check_date = now
        if today_date_str not in completed_date_set:
            check_date = now - timedelta(days=1)

        # Safety bound (max 365 days)
        while streak < 365:
            date_key = check_date.strftime("%Y-%m-%d")
            day_has_completion = any(t.get("completed_at") and str(t["completed_at"]).startswith(date_key) for t in tasks)
            if day_has_completion:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        # Dynamic Motivational Message
        if overdue > 0:
            motivation = f"⚠️ You have {overdue} overdue {'task' if overdue == 1 else 'tasks'} needing attention. Let's tackle them first!"
        elif streak >= 3:
            motivation = f"🔥 You are on fire! You've maintained a {streak}-day completion streak."
        elif completion_rate_overall >= 80 and total > 0:
            motivation = "🌟 Outstanding pace! Over 80% of your coursework is completed."
        elif completed > 0:
            motivation = "🚀 Great momentum! Keep checking off assignments to build your streak."
        else:
            motivation = "💡 Ready to study? Add your deadlines and start checking off tasks!"

        return jsonify({
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": pending,
            "overdue_tasks": overdue,
            "completion_rate_overall": completion_rate_overall,
            "completion_rate_week": completion_rate_week,
            "current_streak_days": streak,
            "priority_breakdown": priority_breakdown,
            "daily_completion_history": daily_history,
            "motivational_message": motivation
        }), 200

    # -------------------------------------------------------------
    # Part B: Monthly Calendar API
    # -------------------------------------------------------------
    @app.route("/api/tasks/calendar", methods=["GET"])
    @login_required
    def get_calendar_tasks():
        """
        Returns tasks grouped by due date for a given month and year.
        Query params: ?month=9&year=2026
        """
        user_id = session["user_id"]
        now = datetime.now()

        try:
            month = int(request.args.get("month", now.month))
            year = int(request.args.get("year", now.year))
            if not (1 <= month <= 12 and 1900 <= year <= 2100):
                return jsonify({"error": "Invalid month or year parameters."}), 400
        except ValueError:
            return jsonify({"error": "Month and year must be integers."}), 400

        month_str = f"{year:04d}-{month:02d}"
        pattern = f"{month_str}%"

        db = db_conn()
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT * FROM tasks
            WHERE user_id = ? AND due_date IS NOT NULL AND due_date != '' AND due_date LIKE ?
            ORDER BY due_date ASC, CASE priority WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END
            """,
            (user_id, pattern)
        )
        rows = cursor.fetchall()
        tasks = [row_to_dict(r) for r in rows]

        calendar_days = {}
        for t in tasks:
            d = t["due_date"]
            if d:
                if d not in calendar_days:
                    calendar_days[d] = []
                calendar_days[d].append(t)

        return jsonify({
            "month": month,
            "year": year,
            "month_name": datetime(year, month, 1).strftime("%B"),
            "days": calendar_days
        }), 200

    # -------------------------------------------------------------
    # Part C: Task Reminders API
    # -------------------------------------------------------------
    @app.route("/api/reminders", methods=["GET"])
    @login_required
    def get_reminders():
        """
        Returns tasks requiring reminders for the authenticated student.
        Safely parses dates without throwing uncaught 500 exceptions.
        """
        user_id = session["user_id"]
        db = db_conn()
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT * FROM tasks
            WHERE user_id = ? AND status = 'Pending' AND due_date IS NOT NULL AND due_date != ''
            """,
            (user_id,)
        )
        rows = cursor.fetchall()
        tasks = [row_to_dict(r) for r in rows]

        today_dt = datetime.now().date()
        reminders = []

        for t in tasks:
            raw_due = str(t["due_date"]).strip() if t.get("due_date") else ""
            if not raw_due:
                continue

            try:
                due_dt = datetime.strptime(raw_due, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                # Skip corrupt or malformed date gracefully without raising 500
                continue

            diff_days = (due_dt - today_dt).days
            is_reminder_due = False
            reminder_reason = ""

            if diff_days < 0:
                is_reminder_due = True
                reminder_reason = f"Overdue by {abs(diff_days)} {'day' if abs(diff_days) == 1 else 'days'}"
            elif diff_days == 0:
                is_reminder_due = True
                reminder_reason = "Due today!"
            elif diff_days == 1 and t.get("reminder_offset") in ("1_day_before", "2_days_before"):
                is_reminder_due = True
                reminder_reason = "Due tomorrow!"
            elif diff_days == 2 and t.get("reminder_offset") == "2_days_before":
                is_reminder_due = True
                reminder_reason = "Due in 2 days"

            if is_reminder_due:
                t_copy = dict(t)
                t_copy["reminder_reason"] = reminder_reason
                t_copy["days_remaining"] = diff_days
                reminders.append(t_copy)

        reminders.sort(key=lambda x: (x["days_remaining"], 0 if x["priority"] == "High" else 1))

        return jsonify({
            "count": len(reminders),
            "reminders": reminders
        }), 200

    return app


# Default app instance
app = create_app()

if __name__ == "__main__":
    if not os.path.exists(DEFAULT_DB_PATH):
        init_db()
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true")
    port = int(os.environ.get("PORT", 5050))
    print(f"Starting Student Task Manager server (debug={debug_mode}) on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=debug_mode)
