# Academic Project Report: Student Task Manager

---

## 1. Project Information

- **Project Title**: Student Task Manager (Full-Stack Academic Coursework & Deadline Tracking Web Application)
- **Author / Student Name**: [Student Name Placeholder]
- **Roll Number / Student ID**: [Student ID Placeholder]
- **Course / Degree**: [Course / Degree Placeholder]
- **Institution**: [Institution Name Placeholder]
- **Date of Submission**: September 2026
- **Technology Stack**: Python (Flask), SQLite3, HTML5, CSS3, JavaScript (ES6+), Pytest

---

## 2. Problem Statement

Academic success in contemporary higher education requires students to balance numerous demanding courses, laboratory assignments, collaborative group projects, and rigid examination schedules. As coursework volumes increase, students often encounter substantial difficulty keeping track of overlapping deadlines, resulting in missed submissions, unnecessary academic stress, and inefficient time allocation.

Existing generic productivity software and commercial project management tools are frequently over-engineered for student needs. They introduce steep learning curves, excessive configuration requirements, and subscription paywalls, or lack dedicated contextual features such as academic priority tracking and due-date status indicators. Conversely, paper notebooks and static notes lack dynamic sorting, search capabilities, and instant task completion metrics.

To overcome these challenges, this project presents the **Student Task Manager**—a lightweight, intuitive, and distraction-free full-stack web application. It provides students with an accessible centralized dashboard to create, categorize, prioritize, update, and monitor academic tasks in real time without external software bloat or unnecessary dependencies.

---

## 3. Project Objectives

The primary objectives of this project are:
1. **Core Task Lifecycle Management**: Deliver full Create, Read, Update, Delete (CRUD) functionality for academic tasks with title, description, priority, due date, and status attributes.
2. **Dynamic Prioritization & Due-Date Tracking**: Implement visual color-coded priority indicators (`High`, `Medium`, `Low`) and automatic deadline notifications (`Overdue`, `Due Today`, `Due Tomorrow`).
3. **Instant Search & Real-Time Filtering**: Allow students to filter tasks instantaneously across multiple criteria (Status and Priority) and execute debounced title/description keyword searches.
4. **Lightweight & Accessible Architecture**: Develop a robust backend with Python/Flask and SQLite, paired with a responsive vanilla HTML/CSS/JS frontend requiring no commercial APIs or heavy frontend frameworks.
5. **Security & Data Integrity**: Ensure parameterized SQL execution against SQL injection, strict server-side input validation, HTML escaping against Cross-Site Scripting (XSS), and database indexing for query performance.
6. **Comprehensive Automated Verification**: Establish a suite of automated unit and integration tests using `pytest` ensuring 100% test pass rates across all REST endpoints.

---

## 4. Development Process

The project followed a disciplined 11-step agile development lifecycle:

1. **Environment Setup**: Configured a Python 3.14 virtual environment (`venv`) with `requirements.txt` containing `Flask` and `pytest`. Configured `.gitignore` to protect environment variables, bytecode, and local database files.
2. **Project Creation & Git Initialization**: Initialized the project directory and Git repository with modular folder separation (`/templates`, `/static/css`, `/static/js`, `/tests`).
3. **Planning & Architecture Design**: Formulated the data model, REST API contracts, and user experience requirements with the AI coding assistant before writing production code.
4. **Database Design & Schema Definition**: Authored `schema.sql` defining the `tasks` table with column constraints (`CHECK` constraints for priority and status) and query optimization indexes (`idx_tasks_status`, `idx_tasks_priority`, `idx_tasks_due_date`).
5. **Database Initialization & Seeding**: Implemented `database.py` with Flask application context connection management and `seed.py` with realistic sample student tasks.
6. **Backend Development (Flask REST API)**: Built `app.py` utilizing the application factory pattern (`create_app`), implementing endpoints for `GET /api/tasks`, `GET /api/tasks/<id>`, `POST /api/tasks`, `PUT /api/tasks/<id>`, `PATCH /api/tasks/<id>/complete`, `DELETE /api/tasks/<id>`, and `GET /api/tasks/search`.
7. **Frontend Development (HTML/CSS/JS)**: Built `templates/index.html`, `static/css/style.css`, and `static/js/app.js` featuring stats cards, an interactive add-task sidebar, filter segments, an edit modal, and toast alerts.
8. **End-to-End Feature Implementation**: Verified that creating, editing, deleting, status toggling, searching, and filtering execute seamlessly across client and server.
9. **Automated Testing**: Created `tests/conftest.py` (temporary SQLite test client fixtures) and `tests/test_api.py` covering all 16 API endpoints and validation edge cases.
10. **Rigorous Code Review & Refactoring**: Conducted a deep code review addressing SQL injection, XSS escaping, strict ISO date parsing, string size bounds, DRY validation, and environment configuration.
11. **Documentation & Final Git Commit**: Authored `README.md` and this project report, verifying final application execution and committing to the Git version control repository.

---

## 5. System Architecture & Request-Response Flow

### System Architecture Diagram (Textual Representation)

```text
+-------------------------------------------------------------------------+
|                          Client (Web Browser)                           |
|  - HTML5 Semantic Structure (templates/index.html)                       |
|  - Responsive CSS3 Styling & Priority Badges (static/css/style.css)      |
|  - Vanilla JS Fetch API, Live Search & DOM Rendering (static/js/app.js) |
+-------------------------------------------------------------------------+
                                    │ ▲
               HTTP Requests (JSON) │ │ HTTP Responses (JSON / HTML)
                                    ▼ │
+-------------------------------------------------------------------------+
|                           Flask Web Server                              |
|  - Application Factory & Routes (app.py)                                 |
|  - Centralized Input Sanitization & Validation                          |
|  - Flask Application Context Connection Management (g object)           |
+-------------------------------------------------------------------------+
                                    │ ▲
                Parameterized SQL   │ │ Row Results (sqlite3.Row)
                                    ▼ │
+-------------------------------------------------------------------------+
|                        SQLite Database (tasks.db)                       |
|  - Table: tasks (id, title, description, priority, due_date, status)    |
|  - Indexes: idx_tasks_status, idx_tasks_priority, idx_tasks_due_date    |
+-------------------------------------------------------------------------+
```

### Request/Response Lifecycle Example: Adding a New Task

1. **User Action**: The student inputs task details (*Title: "CS301 Lab 2", Priority: "High", Due Date: "2026-09-25"*) into the sidebar form and clicks **Add Task**.
2. **Client-Side Event**: `static/js/app.js` intercepts form submission (`e.preventDefault()`), validates non-empty inputs, and sends a `POST` request to `/api/tasks` with a JSON payload.
3. **Server-Side Validation**: `app.py` receives the payload in `create_task()` and executes `validate_and_parse_task_payload()`:
   - Verifies `title` is non-empty and under 150 characters.
   - Verifies `priority` is in `{'Low', 'Medium', 'High'}`.
   - Parses and validates `due_date` format using `datetime.strptime(..., "%Y-%m-%d")`.
4. **Database Execution**: The connection helper `database.get_db()` obtains the SQLite connection. A parameterized `INSERT INTO tasks (title, description, priority, due_date, status) VALUES (?, ?, ?, ?, ?)` query is executed safely.
5. **Server Response**: The server commits the transaction, fetches the created task record, and returns a `201 Created` HTTP response with `{ "message": "Task created successfully.", "task": {...} }`.
6. **DOM Update**: `static/js/app.js` receives the `201` response, triggers a green success toast notification, clears the form, dynamically updates the dashboard stats counters, and prepends the new task card to the UI.

---

## 6. Database Design

The database schema is defined in `schema.sql` utilizing SQLite's native relational engine.

### Table Schema: `tasks`

| Column Name | Data Type | Constraints & Defaults | Description |
| :--- | :--- | :--- | :--- |
| `id` | `INTEGER` | `PRIMARY KEY AUTOINCREMENT` | Unique identifier for each task record |
| `title` | `TEXT` | `NOT NULL` | Short title/name of the academic assignment |
| `description` | `TEXT` | `DEFAULT ''` | Detailed notes, links, or submission instructions |
| `priority` | `TEXT` | `NOT NULL CHECK(priority IN ('Low', 'Medium', 'High')) DEFAULT 'Medium'` | Coursework urgency level |
| `due_date` | `TEXT` | `NULL` | Submission deadline in ISO format (`YYYY-MM-DD`) |
| `status` | `TEXT` | `NOT NULL CHECK(status IN ('Pending', 'Completed')) DEFAULT 'Pending'` | Completion status of the task |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Timestamp of record creation |

### Database Indexes

To ensure high performance as the task list expands, three performance indexes are created:
- `CREATE INDEX idx_tasks_status ON tasks(status);`
- `CREATE INDEX idx_tasks_priority ON tasks(priority);`
- `CREATE INDEX idx_tasks_due_date ON tasks(due_date);`

---

## 7. Features Implemented

1. **Dashboard Overview & Statistics**: Live dashboard displaying aggregate metrics for Total Tasks, Pending Tasks, Completed Tasks, and High-Priority tasks.
2. **Task Creation**: Intuitive sidebar form with client-side and server-side validation.
3. **Interactive Task Cards**: Distinct cards with custom color-coded badges for priorities (Crimson for High, Amber for Medium, Blue for Low) and statuses (Green for Completed, Slate for Pending).
4. **Instant Completion Toggle**: One-click checkbox triggering a `PATCH` request to toggle status between `Pending` and `Completed` with strikethrough visual feedback.
5. **Modal Edit Functionality**: Inline modal dialog enabling modification of task title, notes, priority, due date, and status without page refreshes.
6. **Task Deletion**: Immediate deletion with confirmation dialog to prevent accidental data loss.
7. **Real-Time Debounced Search**: Dynamic filtering as the user types, querying both titles and descriptions.
8. **Segmented Filter Controls**: Instant button-group filtering by status and priority with a one-click reset action.
9. **Smart Date Calculation**: Dynamic tags identifying tasks that are *Overdue*, *Due Today*, or *Due Tomorrow*.
10. **Toast Notification System**: Animated, auto-dismissing toast notifications confirming user actions.

---

## 8. Testing Summary

Automated testing was implemented using `pytest` and Flask's built-in test client with isolated SQLite database instances.

### Automated Test Coverage
- **HTML Route**: Verified `GET /` serves status 200 with proper HTML template rendering.
- **Task Creation**: Tested valid task creation (`201`), missing titles (`400`), invalid priority strings (`400`), malformed due dates (`400`), and oversized title inputs (`400`).
- **Task Retrieval**: Tested single task lookup (`200`), missing ID handling (`404`), and full list retrieval (`200`).
- **Task Update**: Tested valid full updates (`200`) and invalid payload updates (`400`).
- **Status Toggling**: Tested `PATCH /api/tasks/<id>/complete` toggling state forwards and backwards.
- **Task Deletion**: Tested `DELETE /api/tasks/<id>` and verified subsequent 404 lookup.
- **Filtering & Search**: Tested query parameter filters (`?status=`, `?priority=`) and keyword searches (`/api/tasks/search?q=`).

### Actual Pytest Execution Output

```text
$ pytest -v
============================= test session starts ==============================
platform darwin -- Python 3.14.7, pytest-8.3.2, pluggy-1.6.0
rootdir: /Users/sanjiv215/Desktop/Projects/IITP/student-task-manager
collected 16 items

tests/test_api.py::test_index_page PASSED                                [  6%]
tests/test_api.py::test_create_task_success PASSED                       [ 12%]
tests/test_api.py::test_create_task_validation_missing_title PASSED      [ 18%]
tests/test_api.py::test_create_task_validation_invalid_priority PASSED   [ 25%]
tests/test_api.py::test_create_task_validation_invalid_due_date PASSED   [ 31%]
tests/test_api.py::test_create_task_validation_oversized_title PASSED    [ 37%]
tests/test_api.py::test_get_single_task PASSED                           [ 43%]
tests/test_api.py::test_get_task_not_found PASSED                        [ 50%]
tests/test_api.py::test_list_all_tasks PASSED                            [ 56%]
tests/test_api.py::test_update_task PASSED                               [ 62%]
tests/test_api.py::test_update_task_invalid_payload PASSED               [ 68%]
tests/test_api.py::test_toggle_complete_task PASSED                      [ 75%]
tests/test_api.py::test_delete_task PASSED                               [ 81%]
tests/test_api.py::test_filter_tasks_by_status PASSED                    [ 87%]
tests/test_api.py::test_filter_tasks_by_priority PASSED                  [ 93%]
tests/test_api.py::test_search_tasks_by_title_and_description PASSED     [100%]

============================== 16 passed in 0.08s ==============================
```

---

## 9. Deliverable Screenshots

*Insert project screenshots into the placeholders below before final submission:*

### Screenshot 1: Home/Dashboard
<!-- ![Screenshot 1: Home/Dashboard](screenshots/01_dashboard.png) -->
*Caption: Student Task Manager main page featuring real-time overview metrics and dashboard layout.*

---

### Screenshot 2: Add Task
<!-- ![Screenshot 2: Add Task](screenshots/02_add_task.png) -->
*Caption: Form for entering task title, priority, due date, and supplementary description.*

---

### Screenshot 3: Task List
<!-- ![Screenshot 3: Task List](screenshots/03_task_list.png) -->
*Caption: Display of all active student tasks with visual color-coded priority indicators.*

---

### Screenshot 4: Edit/Update Task
<!-- ![Screenshot 4: Edit/Update Task](screenshots/04_edit_task.png) -->
*Caption: Interactive edit modal pre-filled with task details for seamless modification.*

---

### Screenshot 5: Task Completed
<!-- ![Screenshot 5: Task Completed](screenshots/05_completed_task.png) -->
*Caption: Academic task marked as Completed with green badge and crossed-out title styling.*

---

### Screenshot 6: Filter/Search
<!-- ![Screenshot 6: Filter/Search](screenshots/06_filter_search.png) -->
*Caption: Real-time filtering and live search showing only High Priority coursework matching keywords.*

---

### Screenshot 7: Database
<!-- ![Screenshot 7: Database](screenshots/07_database.png) -->
*Caption: SQLite tasks table viewed in DB Browser for SQLite showing structured relational data.*

---

### Screenshot 8: Testing Output
<!-- ![Screenshot 8: Testing Output](screenshots/08_testing_output.png) -->
*Caption: Terminal window demonstrating all 16 automated pytest tests passing successfully.*

---

### Screenshot 9: Claude Code / Antigravity Interaction
<!-- ![Screenshot 9: AI Interaction](screenshots/09_ai_interaction.png) -->
*Caption: AI pair programming session assisting with architecture, code review, and automated testing.*

---

### Screenshot 10: Final Application
<!-- ![Screenshot 10: Final Application](screenshots/10_final_application.png) -->
*Caption: Fully working Student Task Manager web application running locally in the browser.*

---

## 10. Challenges Faced & AI-Assisted Development Reflection

During the development process, challenges arose regarding state synchronization between the frontend filtering controls, maintaining accurate live task counter statistics without generating redundant network roundtrips, and handling SQLite application context lifecycles cleanly within Flask. 

Collaborating with the AI coding assistant (Claude Code / Antigravity) accelerated resolution of these bottlenecks. The assistant provided immediate architectural guidance by introducing a centralized payload validation helper, designing modular pytest fixtures using isolated temporary databases, and structuring the frontend JavaScript with local state caching. This pair-programming workflow ensured clean separation of concerns, robust security practices, and reliable full-stack execution.

---

## 11. Conclusion

The **Student Task Manager** project successfully fulfills all initial functional and non-functional requirements. It delivers a fast, responsive, and secure web application that enables students to organize coursework, monitor deadlines, and prioritize tasks effectively. Built using clean Python, Flask, SQLite, and vanilla frontend technologies, the application demonstrates solid full-stack engineering principles, thorough automated test coverage, and a distraction-free user experience.
