# 🎓 Student Task Manager

A lightweight, beginner-friendly, and fully functional full-stack web application designed for students to organize, prioritize, update, and track their academic assignments, lab reports, and exam deadlines.

---

## 🚀 Features

- **Task Management (CRUD)**:
  - **Create**: Add tasks with title, description, priority (Low / Medium / High), and due dates.
  - **Read/List**: View all academic tasks organized in clean cards with color-coded priority badges.
  - **Edit/Update**: Modify task details in a pre-populated modal dialog without reloading.
  - **Delete**: Remove tasks with confirmation dialogs.
  - **Toggle Completion**: One-click checkbox or button to toggle tasks between `Pending` and `Completed`.
- **Live Summary Statistics**: Real-time counter cards showing Total, Pending, Completed, and High-priority tasks.
- **Search & Filtering**:
  - Real-time debounced search by title and description.
  - Status filter buttons (`All`, `Pending`, `Completed`).
  - Priority filter buttons (`All`, `High`, `Medium`, `Low`).
  - One-click "Reset Filters" button.
- **Due Date Badges**: Automatic dynamic highlighting for tasks that are *Overdue*, *Due Today*, or *Due Tomorrow*.
- **Modern Responsive Design**: Clean vanilla CSS with no bulky external frontend frameworks needed.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask 3.0.3
- **Database**: SQLite3 (native standard library)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+ with `fetch` API)
- **Testing**: `pytest` 8.3.2 with isolated temporary SQLite databases

---

## 📁 Project Structure

```text
student-task-manager/
├── .gitignore             # Git ignore patterns for Python, venv, and SQLite files
├── requirements.txt       # Python package dependencies (Flask, pytest)
├── app.py                 # Flask app factory, frontend route, and REST API endpoints
├── database.py            # SQLite connection helper & schema executor
├── schema.sql             # SQL table definitions for tasks
├── seed.py                # Database seed script with sample academic tasks
├── static/
│   ├── css/
│   │   └── style.css      # Modern responsive styling & priority badges
│   └── js/
│       └── app.js         # Vanilla JS API interactions, live search, filters, modals
├── templates/
│   └── index.html         # Main dashboard HTML template
├── tests/
│   ├── __init__.py
│   ├── conftest.py        # Pytest fixtures (in-memory/temporary test DB client)
│   └── test_api.py        # 13 comprehensive API and validation tests
└── README.md              # Project documentation and guide
```

---

## 📦 Setup & Installation

### 1. Clone or Navigate to the Project
```bash
cd student-task-manager
```

### 2. Create and Activate Virtual Environment
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- **Windows**:
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Seed Sample Academic Data
```bash
python seed.py
```

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Running Automated Tests

Run the full pytest test suite:
```bash
pytest -v
```

---

## 📡 REST API Reference

| Method | Endpoint | Description | Request Body Example | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Serves dashboard web page | None | `200` |
| `GET` | `/api/tasks` | List all tasks (supports `?status=` & `?priority=`) | None | `200`, `400` |
| `GET` | `/api/tasks/<id>` | Get task by ID | None | `200`, `404` |
| `POST` | `/api/tasks` | Create a new task | `{"title": "Math HW", "priority": "High", "due_date": "2026-09-20"}` | `201`, `400` |
| `PUT` | `/api/tasks/<id>` | Update existing task | `{"title": "Updated", "priority": "Low", "status": "Completed"}` | `200`, `400`, `404` |
| `PATCH`| `/api/tasks/<id>/complete` | Toggle or set completion | `{"completed": true}` *(or empty to toggle)* | `200`, `404` |
| `DELETE`| `/api/tasks/<id>` | Delete task | None | `200`, `404` |
| `GET` | `/api/tasks/search?q=` | Search title/description | None | `200` |

---

## 📖 User Guide (How to Use)

1. **Add a Task**: Fill out the form in the left sidebar (Title is required, pick priority and due date) and click **Add Task**.
2. **Mark Complete / Incomplete**: Click the checkbox next to any task title.
3. **Edit a Task**: Click the **✏️ Edit** button on the task card to open the modal, update fields, and click **Save Changes**.
4. **Delete a Task**: Click the **🗑️ Delete** button and confirm the browser prompt.
5. **Search Tasks**: Type any keyword into the search bar at the top of the task list (results update instantly).
6. **Filter Tasks**: Click on any status (`Pending`, `Completed`) or priority (`High`, `Med`, `Low`) button in the toolbar. Click **Reset Filters** to clear.

---

## 📸 Deliverable Screenshots

*(Insert your captured screenshots here)*

1. **Home/Dashboard** - Main page with task overview and statistics.
   <!-- ![Dashboard](screenshots/01_dashboard.png) -->
2. **Add Task** - The add-task form filled in with sample academic data.
   <!-- ![Add Task](screenshots/02_add_task.png) -->
3. **Task List** - All pending and completed tasks displayed.
   <!-- ![Task List](screenshots/03_task_list.png) -->
4. **Edit/Update Task** - The edit modal open or a task after being edited.
   <!-- ![Edit Task](screenshots/04_edit_task.png) -->
5. **Task Completed** - A task marked as completed with green badge and line-through styling.
   <!-- ![Completed Task](screenshots/05_completed_task.png) -->
6. **Filter/Search** - Tasks filtered by priority (e.g., High) or searched by keyword.
   <!-- ![Filter Search](screenshots/06_filter_search.png) -->
7. **Database** - The SQLite `tasks` table viewed in DB Browser for SQLite or SQLite CLI.
   <!-- ![Database](screenshots/07_database.png) -->
8. **Testing Output** - Terminal output showing all 13 `pytest` tests passing.
   <!-- ![Pytest Output](screenshots/08_pytest_output.png) -->
9. **Antigravity / Coding Assistant Interaction** - Screenshot of this development session.
   <!-- ![Assistant Interaction](screenshots/09_antigravity.png) -->
10. **Final Application** - Full view of the completed, working app in the browser.
    <!-- ![Final Application](screenshots/10_final_app.png) -->
