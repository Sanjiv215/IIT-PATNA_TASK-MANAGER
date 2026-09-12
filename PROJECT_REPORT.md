# Academic Project Report: Student Task Manager

---

## 1. Project Information

- **Project Title**: Student Task Manager (Full-Stack Multi-User Academic Coursework & Deadline Tracking Web Application)
- **Author / Student Name**: [Student Name Placeholder]
- **Roll Number / Student ID**: [Student ID Placeholder]
- **Course / Degree**: [Course / Degree Placeholder]
- **Institution**: [Institution Name Placeholder]
- **Date of Submission**: September 2026
- **Technology Stack**: Python (Flask), SQLite3, HTML5, CSS3, JavaScript (ES6+), Pytest, Werkzeug Security, Gunicorn

---

## 2. Problem Statement

Academic success in contemporary higher education requires students to balance numerous demanding courses, laboratory assignments, collaborative group projects, and rigid examination schedules. As coursework volumes increase, students often encounter substantial difficulty keeping track of overlapping deadlines, resulting in missed submissions, unnecessary academic stress, and inefficient time allocation.

Existing generic productivity software and commercial project management tools are frequently over-engineered for student needs. They introduce steep learning curves, excessive configuration requirements, and subscription paywalls, or lack dedicated contextual features such as academic priority tracking and due-date status indicators. Furthermore, shared computers in academic libraries and computer labs require personal authenticated student accounts with strict data isolation.

To overcome these challenges, this project presents the **Student Task Manager**—a lightweight, intuitive, and distraction-free full-stack web application. It provides students with a secure personal dashboard to create, categorize, prioritize, update, and monitor academic tasks in real time with complete data isolation and no external framework bloat.

---

## 3. Project Objectives

The primary objectives of this project are:
1. **User Authentication & Data Isolation**: Implement secure registration (`/signup`), login (`/login`), and logout (`/logout`) using password hashing (`werkzeug.security`) and session-based state management, ensuring no student can access or modify another student's coursework.
2. **Core Task Lifecycle Management**: Deliver full Create, Read, Update, Delete (CRUD) functionality for academic tasks with title, description, priority, due date, and status attributes.
3. **Dynamic Prioritization & Due-Date Tracking**: Implement visual color-coded priority indicators (`High`, `Medium`, `Low`) and automatic deadline notifications (`Overdue`, `Due Today`, `Due Tomorrow`).
4. **Instant Search & Real-Time Filtering**: Allow students to filter tasks instantaneously across multiple criteria (Status and Priority) and execute debounced title/description keyword searches.
5. **Modern Linear-Inspired Minimalist UI**: Design a unified, responsive interface featuring top navigation, quick summary metrics, unified task modals, custom animated checkboxes, and mobile-friendly layouts.
6. **Comprehensive Automated Verification**: Establish a suite of automated unit and integration tests using `pytest` verifying 100% test pass rates across authentication, validation, route protection, and task CRUD.

---

## 4. Development Process

The project followed a disciplined agile development lifecycle:

1. **Environment Setup & Configuration**: Configured a Python 3.14 virtual environment (`venv`) with `Flask`, `werkzeug`, `gunicorn`, and `pytest`.
2. **Project Creation & Git Initialization**: Initialized the project repository with clean modular separation (`/templates`, `/static/css`, `/static/js`, `/tests`).
3. **Initial Architecture & Planning**: Designed initial single-user task CRUD models and REST API contracts.
4. **Database Design & Schema Definition**: Authored `schema.sql` defining relational tables (`users`, `tasks`) with foreign keys, constraints, and query indexes (`idx_users_email`, `idx_tasks_user_id`, `idx_tasks_status`, `idx_tasks_priority`, `idx_tasks_due_date`).
5. **Database Migration & Seeding**: Implemented `database.py` with automatic schema migrations and `seed.py` with a demo student account (`demo@student.edu`) and realistic coursework.
6. **Authentication & Backend Development**: Built `app.py` utilizing the application factory pattern, `@login_required` decorator, session management, brute-force login throttling, and user-isolated API endpoints.
7. **Frontend Development & UI Redesign**: Crafted modern templates (`login.html`, `signup.html`, `index.html`), a Linear-inspired CSS system (`style.css`), and dynamic vanilla JavaScript (`app.js`).
8. **End-to-End Feature Verification**: Verified all workflows (signup, login, task create, modal edit, checkbox toggle, search, filter, logout) execute smoothly.
9. **Automated Testing Suite**: Created `tests/conftest.py` and `tests/test_api.py` with 15 comprehensive test cases covering registration validation, authentication, route protections, and user isolation.
10. **Code Review & Security Hardening**: Validated SQL parameterization, XSS escaping, ISO date validation, string boundaries, and rate limiting.
11. **Production Deployment Configuration**: Added `Procfile`, `runtime.txt`, and Gunicorn support for one-click cloud deployment.

---

## 5. System Architecture & Request-Response Flow

### System Architecture Diagram (Textual Representation)

```text
+-------------------------------------------------------------------------+
|                          Client (Web Browser)                           |
|  - HTML5 Pages: Login, Signup, Dashboard (templates/*.html)             |
|  - Linear-Inspired Modern CSS3 Styling (static/css/style.css)           |
|  - Vanilla JS Fetch API, Modal & Live Filters (static/js/app.js)        |
+-------------------------------------------------------------------------+
                                    │ ▲
               HTTP Requests (JSON) │ │ HTTP Responses (JSON / HTML)
                                    ▼ │
+-------------------------------------------------------------------------+
|                           Flask Web Server                              |
|  - App Factory & Routes: /login, /signup, /logout, /api/tasks (app.py)  |
|  - Session Authentication & @login_required Decorator                   |
|  - Password Hashing (werkzeug.security) & Centralized Sanitization      |
|  - Flask Application Context Connection Management (g object)           |
+-------------------------------------------------------------------------+
                                    │ ▲
                Parameterized SQL   │ │ Row Results (sqlite3.Row)
                                    ▼ │
+-------------------------------------------------------------------------+
|                        SQLite Database (tasks.db)                       |
|  - Users Table: id, name, email, password_hash, created_at              |
|  - Tasks Table: id, user_id (FK), title, description, priority, due_date|
|  - Performance Indexes: user_id, email, status, priority, due_date      |
+-------------------------------------------------------------------------+
```

### Request/Response Lifecycle Example: Creating a Task with User Isolation

1. **User Action**: An authenticated student clicks **+ New Task** in the navbar, enters assignment details in the modal (*Title: "CS301 Lab 2", Priority: "High", Due Date: "2026-09-25"*), and clicks **Save Task**.
2. **Client-Side Event**: `static/js/app.js` sends a `POST` request to `/api/tasks` with JSON payload. The browser automatically includes the signed Flask session cookie.
3. **Session & Auth Check**: The `@login_required` decorator extracts `session["user_id"]`. If missing, it immediately aborts with `401 Unauthorized`.
4. **Server-Side Validation**: `app.py` parses and validates the payload, ensuring non-empty title (< 150 chars), valid priority enum, and strict `YYYY-MM-DD` date formatting.
5. **Isolated Database Insertion**: The server executes `INSERT INTO tasks (user_id, title, description, priority, due_date, status) VALUES (?, ?, ?, ?, ?, ?)` binding `session["user_id"]`.
6. **Server Response**: The server commits the transaction and returns `201 Created` with `{ "message": "Task created successfully.", "task": {...} }`.
7. **DOM Update**: `static/js/app.js` closes the modal, triggers a green toast notification, updates live summary counters, and renders the new task card in the feed.

---

## 6. Database Design

The relational schema is implemented in SQLite with table constraints and foreign key relationships.

### 1. `users` Table
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique student account identifier |
| `name` | `TEXT` | `NOT NULL` | Full student name |
| `email` | `TEXT` | `NOT NULL UNIQUE` | Unique academic email address |
| `password_hash` | `TEXT` | `NOT NULL` | Secure password hash |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Account creation timestamp |

### 2. `tasks` Table
| Column Name | Data Type | Constraints & Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique task identifier |
| `user_id` | `INTEGER` | `NOT NULL REFERENCES users(id) ON DELETE CASCADE` | Foreign key linking task to user |
| `title` | `TEXT` | `NOT NULL` | Short title of assignment |
| `description` | `TEXT` | `DEFAULT ''` | Detailed notes or instructions |
| `priority` | `TEXT` | `NOT NULL CHECK(priority IN ('Low', 'Medium', 'High')) DEFAULT 'Medium'` | Coursework urgency level |
| `due_date` | `TEXT` | `NULL` | Submission deadline (`YYYY-MM-DD`) |
| `status` | `TEXT` | `NOT NULL CHECK(status IN ('Pending', 'Completed')) DEFAULT 'Pending'` | Completion status |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Record creation timestamp |

---

## 7. Features Implemented

1. **User Authentication**: Secure signup with name, email, password length, and confirmation matching; login with credential checking and password visibility toggle; secure logout.
2. **Strict User Isolation**: Database queries enforce user isolation; no student can access or manipulate another student's coursework.
3. **Linear-Inspired UI Overhaul**: Modern navigation bar, user avatar pill, stat metric cards, custom checkboxes, and responsive layout.
4. **Unified Task Modal**: Modal dialog for creating and modifying tasks without losing page context.
5. **Live Statistics Strip**: Dynamic counters for Total Coursework, Pending Tasks, Completed Tasks, and Overdue Tasks.
6. **Task Status Toggle**: Instant checkbox toggling with emerald status pill and strikethrough styling.
7. **Debounced Real-Time Search**: Substring filtering across task titles and descriptions.
8. **Segmented Filter Controls**: Instant button-group filtering by status and priority with one-click reset.
9. **Smart Due-Date Flags**: Dynamic visual tags for *Overdue*, *Due Today*, and *Due Tomorrow*.
10. **Toast Notification System**: Animated feedback banners for every user action.

---

## 8. Testing Summary

Automated testing was implemented using `pytest` with isolated temporary SQLite databases.

### Actual Pytest Execution Output

```text
$ pytest -v
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-8.3.2, pluggy-1.6.0
rootdir: /Users/sanjiv215/Desktop/Projects/IITP/student-task-manager
collected 15 items

tests/test_api.py::test_signup_success PASSED                            [  6%]
tests/test_api.py::test_signup_validation_missing_name PASSED            [ 13%]
tests/test_api.py::test_signup_validation_invalid_email PASSED           [ 20%]
tests/test_api.py::test_signup_validation_short_password PASSED          [ 26%]
tests/test_api.py::test_signup_validation_password_mismatch PASSED       [ 33%]
tests/test_api.py::test_signup_validation_duplicate_email PASSED         [ 40%]
tests/test_api.py::test_login_success_and_logout PASSED                  [ 46%]
tests/test_api.py::test_login_invalid_credentials PASSED                 [ 53%]
tests/test_api.py::test_unauthenticated_api_protection PASSED            [ 60%]
tests/test_api.py::test_user_data_isolation PASSED                       [ 66%]
tests/test_api.py::test_create_task_authenticated PASSED                 [ 73%]
tests/test_api.py::test_task_validation_errors PASSED                    [ 80%]
tests/test_api.py::test_update_and_toggle_complete PASSED                [ 86%]
tests/test_api.py::test_delete_task_authenticated PASSED                 [ 93%]
tests/test_api.py::test_filter_and_search_tasks PASSED                   [100%]

============================== 15 passed in 0.71s ==============================
```

---

## 9. Deliverable Screenshots

*Insert project screenshots into the placeholders below before final submission:*

### Screenshot 1: Home/Dashboard
<!-- ![Screenshot 1: Home/Dashboard](screenshots/01_dashboard.png) -->
*Caption: Redesigned dashboard displaying header navbar with user pill, stats metric strip, and task list feed.*

---

### Screenshot 2: Add Task
<!-- ![Screenshot 2: Add Task](screenshots/02_add_task.png) -->
*Caption: Unified modal window for adding new coursework with priority selector and deadline picker.*

---

### Screenshot 3: Task List
<!-- ![Screenshot 3: Task List](screenshots/03_task_list.png) -->
*Caption: Main task feed rendering student tasks with custom checkboxes and color-coded priority badges.*

---

### Screenshot 4: Edit/Update Task
<!-- ![Screenshot 4: Edit/Update Task](screenshots/04_edit_task.png) -->
*Caption: Interactive edit modal pre-filled with existing task data for inline modifications.*

---

### Screenshot 5: Task Completed
<!-- ![Screenshot 5: Task Completed](screenshots/05_completed_task.png) -->
*Caption: Academic task marked as Completed with green status pill and strikethrough title styling.*

---

### Screenshot 6: Filter/Search
<!-- ![Screenshot 6: Filter/Search](screenshots/06_filter_search.png) -->
*Caption: Dashboard filtering tasks in real time by High Priority and keyword search.*

---

### Screenshot 7: Database
<!-- ![Screenshot 7: Database](screenshots/07_database.png) -->
*Caption: SQLite database tables (users and tasks) viewed in DB Browser for SQLite showing relational schema.*

---

### Screenshot 8: Testing Output
<!-- ![Screenshot 8: Testing Output](screenshots/08_testing_output.png) -->
*Caption: Terminal output demonstrating 15 passing automated pytest test cases covering auth and task CRUD.*

---

### Screenshot 9: Login Screen
<!-- ![Screenshot 9: Login Screen](screenshots/09_login_screen.png) -->
*Caption: Clean student authentication login page with show/hide password toggle and demo credentials.*

---

### Screenshot 10: Sign Up Screen
<!-- ![Screenshot 10: Sign Up Screen](screenshots/10_signup_screen.png) -->
*Caption: Student account registration screen with full name, academic email, and password validation.*

---

### Screenshot 11: Claude Code / Antigravity Interaction
<!-- ![Screenshot 11: AI Interaction](screenshots/11_ai_interaction.png) -->
*Caption: AI pair programming session assisting with auth architecture, UI redesign, and test automation.*

---

### Screenshot 12: Final Application
<!-- ![Screenshot 12: Final Application](screenshots/12_final_application.png) -->
*Caption: Complete working Student Task Manager web application running with authenticated multi-user support.*

---

## 10. Challenges Faced & AI-Assisted Development Reflection

Adding multi-user authentication to an existing codebase required careful architectural planning to ensure backwards compatibility, non-destructive database migrations for existing task records, and bulletproof user data isolation. Collaborating with the AI coding assistant (Claude Code / Antigravity) accelerated the design of clean database migration routines, session authentication decorators, and comprehensive pytest fixtures that test both authenticated and unauthorized states. Additionally, the AI assisted in establishing a modern Linear-inspired design system with CSS custom properties, ensuring cohesive aesthetics across authentication screens and the dashboard.

---

## 11. Conclusion

The **Student Task Manager** project represents a complete, secure, and modern full-stack web application. By integrating robust session-based authentication, strict data isolation, intuitive task management workflows, and a refined Linear-inspired user interface, the application equips students with an effective, distraction-free tool to manage their academic coursework and deadlines with confidence.
