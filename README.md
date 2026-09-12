# 🎓 Student Task Manager

> A lightweight, intuitive full-stack web application designed for students to organize, prioritize, track, and manage academic coursework, deadlines, and project milestones.

🔗 **Live Demo URL**: `https://student-task-manager-<your-subdomain>.onrender.com` *(or your deployed URL)*

---

## 📌 Problem Statement

College and high school students frequently juggle multiple simultaneous courses, lab assignments, project milestones, and exam dates. Without a centralized and lightweight tracking tool, deadlines are easily missed, and prioritizing urgent vs. low-priority coursework becomes overwhelming. Traditional productivity tools are often overly complex or bloated with unnecessary features.

The **Student Task Manager** solves this problem by providing a clean, responsive, distraction-free dashboard where students can quickly create tasks, set priority levels, assign due dates, track progress in real-time, search instantly, and filter tasks without page reloads.

---

## ✨ Features

- **Full Task Lifecycle Management (CRUD)**:
  - **Create**: Add tasks with title, description, priority (`Low`, `Medium`, `High`), and due date.
  - **Read**: View tasks neatly organized into interactive cards with color-coded priority and status badges.
  - **Update**: Edit existing tasks in place using a pre-populated modal dialog.
  - **Delete**: Remove tasks with safety confirmation prompts.
  - **Toggle Status**: Instantly mark tasks as `Completed` or `Pending` with a single checkbox toggle.
- **Live Summary Statistics**: Dynamic real-time counters displaying Total Tasks, Pending Tasks, Completed Tasks, and High-Priority tasks.
- **Real-Time Instant Search**: Live debounced search by title and description keywords.
- **Multi-Criteria Filtering**: Instant filtering by Status (`All`, `Pending`, `Completed`) and Priority (`All`, `High`, `Medium`, `Low`), plus a one-click **Reset Filters** button.
- **Smart Due-Date Indicators**: Automatically flags tasks as *Overdue*, *Due Today*, or *Due Tomorrow*.
- **Toast Notifications**: Non-intrusive feedback toasts for every user action (create, update, toggle, delete).
- **Responsive & Modern Vanilla UI**: Clean, mobile-friendly design built with pure CSS and zero external heavyweight UI dependencies.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask 3.0.3, Gunicorn 22.0.0
- **Database**: SQLite3 (embedded relational database with connection management on Flask context)
- **Frontend**: Vanilla HTML5, modern responsive CSS3, vanilla JavaScript (ES6+ with `fetch` API)
- **Testing**: `pytest` 8.3.2 with isolated temporary SQLite database fixtures

---

## 📁 Project Structure

```text
student-task-manager/
├── .gitignore             # Ignores Python bytecode, venv, SQLite .db files, and environment configs
├── requirements.txt       # Core project dependencies (Flask, gunicorn, pytest)
├── Procfile               # Production WSGI entry point for Render/Railway (web: gunicorn app:app)
├── runtime.txt            # Explicit Python runtime specification (python-3.11.9)
├── app.py                 # Flask application factory, frontend rendering, and RESTful API endpoints
├── database.py            # SQLite database connection manager and schema initializer
├── schema.sql             # Database schema definition with constraints and performance indexes
├── seed.py                # Database seeding script with realistic sample academic tasks
├── templates/
│   └── index.html         # Semantic single-page dashboard HTML template
├── static/
│   ├── css/
│   │   └── style.css      # Custom stylesheet with modern design system and priority badges
│   └── js/
│       └── app.js         # Vanilla JavaScript handling API calls, live search, filters, and DOM updates
├── tests/
│   ├── __init__.py        # Test package marker
│   ├── conftest.py        # Pytest fixtures for application test client and temporary DB
│   └── test_api.py        # Comprehensive test suite covering all 16 API and validation scenarios
├── PROJECT_REPORT.md      # Formal academic project report document
└── README.md              # Project overview, documentation, setup guide, and screenshot checklist
```

---

## 🚀 Setup & Local Installation

### 1. Clone or Open the Repository
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
Populate the SQLite database with sample coursework:
```bash
python seed.py
```

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🌐 Free-Tier Cloud Deployment Guide (Render)

This application is fully production-configured with `gunicorn`, `Procfile`, and `runtime.txt` for one-click deployment on **Render** (Free Tier):

### Quick Deployment Steps:
1. Push this `student-task-manager` repository to your **GitHub** account.
2. Sign up / Log in to [Render.com](https://render.com).
3. In the Render Dashboard, click **New +** > **Web Service**.
4. Select **Build and deploy from a Git repository** and connect your `student-task-manager` repo.
5. Configure the service settings:
   - **Name**: `student-task-manager` (or custom)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: `Free`
6. Click **Deploy Web Service**.
7. Once deployed, Render will provide a live URL (`https://<service-name>.onrender.com`).

> **Note on SQLite on Free-Tier Hosting**:  
> Render's free tier uses an ephemeral filesystem, meaning if the application is rebuilt or redeployed, the local SQLite database resets. To ensure uninterrupted demonstration, our `app.py` automatically initializes tables and seeds standard sample tasks on initial startup.

---

## 📡 REST API Reference

| Method | Endpoint | Description | Example Request Body | Example Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Serves dashboard HTML page | *None* | `200 OK` (HTML) |
| `GET` | `/api/tasks` | List all tasks (supports `?status=` & `?priority=`) | *None* | `[{"id": 1, "title": "CS201 Assignment", "priority": "High", "status": "Pending", ...}]` |
| `GET` | `/api/tasks/<id>` | Get single task details | *None* | `{"id": 1, "title": "CS201 Assignment", ...}` (or `404`) |
| `POST` | `/api/tasks` | Create a new task | `{"title": "Physics Lab", "priority": "Medium", "due_date": "2026-09-20"}` | `{"message": "Task created successfully.", "task": {...}}` (`201`) |
| `PUT` | `/api/tasks/<id>` | Update existing task | `{"title": "Physics Lab Report", "priority": "High", "status": "Pending"}` | `{"message": "Task updated successfully.", "task": {...}}` (`200`) |
| `PATCH` | `/api/tasks/<id>/complete` | Toggle task completion | `{"completed": true}` *(or empty body to toggle)* | `{"message": "Task marked as Completed.", "task": {...}}` (`200`) |
| `DELETE` | `/api/tasks/<id>` | Delete task by ID | *None* | `{"message": "Task 1 deleted successfully."}` (`200`) |
| `GET` | `/api/tasks/search` | Search tasks by title or description | *Query param:* `?q=calculus` | `[{"id": 2, "title": "Calculus HW", ...}]` (`200`) |

---

## 📖 User Guide (For End Users)

- **Adding a Task**: In the "Add New Task" section on the left, enter your task title (required), optional notes, priority level (`Low`, `Medium`, `High`), and target due date. Click **Add Task**.
- **Marking as Complete**: Click the checkbox on any task card. The task will instantly update to `Completed` with a green badge and strikethrough styling.
- **Editing a Task**: Click the **✏️ Edit** button on the card. An edit window will open pre-filled with your task details. Make your adjustments and click **Save Changes**.
- **Deleting a Task**: Click the **🗑️ Delete** button on the card and confirm the popup dialog.
- **Searching**: Start typing in the search bar at the top of the task list. The list filters instantly as you type.
- **Filtering**: Click on any status pill (`Pending`, `Completed`) or priority pill (`High`, `Med`, `Low`) in the toolbar. To clear all filters, click **Reset Filters**.

---

## 🧪 Testing

The test suite is built with `pytest` and uses temporary, isolated SQLite databases to test all REST API routes and data validation rules.

To run the test suite:
```bash
pytest -v
```

---

## 📸 Deliverable Screenshots

1. **Home/Dashboard – Student Task Manager main page**  
   <!-- ![Screenshot 1: Home/Dashboard](screenshots/01_dashboard.png) -->
   *Caption: Main application dashboard displaying header, real-time statistics counters, task creation sidebar, and active task cards.*

2. **Add Task – form for entering task title, priority, and due date**  
   <!-- ![Screenshot 2: Add Task](screenshots/02_add_task.png) -->
   *Caption: Task creation form populated with sample academic assignment details and priority selection.*

3. **Task List – display of all pending and completed tasks**  
   <!-- ![Screenshot 3: Task List](screenshots/03_task_list.png) -->
   *Caption: Main task feed rendering multiple tasks with color-coded priority badges and due-date status.*

4. **Edit/Update Task – modified task details**  
   <!-- ![Screenshot 4: Edit/Update Task](screenshots/04_edit_task.png) -->
   *Caption: Interactive edit modal pre-filled with existing task data for inline modifications.*

5. **Task Completed – task marked as completed**  
   <!-- ![Screenshot 5: Task Completed](screenshots/05_completed_task.png) -->
   *Caption: Task card updated to Completed state with green status pill and crossed-out title.*

6. **Filter/Search – tasks filtered by priority or status**  
   <!-- ![Screenshot 6: Filter/Search](screenshots/06_filter_search.png) -->
   *Caption: Dashboard filtering tasks in real time by High Priority and keyword search.*

7. **Database – SQLite database showing stored tasks**  
   <!-- ![Screenshot 7: Database](screenshots/07_database.png) -->
   *Caption: SQLite tasks table viewed in DB Browser for SQLite showing schema structure and populated records.*

8. **Testing Output – terminal showing successful pytest results**  
   <!-- ![Screenshot 8: Testing Output](screenshots/08_testing_output.png) -->
   *Caption: Terminal output demonstrating 16 passing automated pytest test cases with 100% pass rate.*

9. **Claude Code/Antigravity Interaction – AI assisting with implementation/debugging**  
   <!-- ![Screenshot 9: AI Interaction](screenshots/09_ai_interaction.png) -->
   *Caption: Pair programming session with AI assistant guiding architecture design, code review, and automated testing.*

10. **Final Application – complete working application in the browser**  
    <!-- ![Screenshot 10: Final Application](screenshots/10_final_application.png) -->
    *Caption: Complete end-to-end working Student Task Manager web application running locally or in cloud.*

---

## 🔮 Future Improvements

1. **Email & Desktop Due-Date Reminders**: Automated notifications alerting students 24 hours prior to upcoming assignment deadlines.
2. **User Authentication & Multi-User Support**: Secure login/signup system with role-based isolation (personal student workspaces).
3. **Course & Subject Categories**: Tagging tasks by academic course codes (e.g., `CS101`, `MATH202`) with color-coded subject groupings.

---

## 👥 Author & Credits

- **Developer**: [Student Name Placeholder]
- **Technology Stack**: Python / Flask, SQLite, Vanilla HTML5 / CSS3 / JavaScript
- **Deployment**: Render / Gunicorn
- **AI Pair Programming Assistant**: Google DeepMind Antigravity / Claude Code
