# 🎓 Student Task Manager

> A modern, lightweight full-stack web application for students to organize, prioritize, track, and manage academic coursework, deadlines, learning analytics, and calendar milestones with secure multi-user authentication.

🔗 **Live Demo URL**: `https://student-task-manager-<your-subdomain>.onrender.com` *(or your deployed URL)*

---

## 📌 Problem Statement

College and high school students frequently juggle multiple simultaneous courses, lab assignments, project milestones, and exam dates. Without a centralized and lightweight tracking tool, deadlines are easily missed, and prioritizing urgent vs. low-priority coursework becomes overwhelming. Traditional productivity tools are often overly complex or bloated with unnecessary features.

The **Student Task Manager** provides a distraction-free, personal student workspace to organize assignments, visualize deadlines on an interactive monthly calendar, analyze completion velocity with weekly streaks, set deadline reminders, and filter tasks in real-time.

---

## ✨ Features

- **🔐 Multi-User Authentication & Security**:
  - Secure student registration (`/signup`) and login (`/login`) with session management.
  - Strict user data isolation: every task belongs to `user_id`.
  - Passwords hashed using `werkzeug.security` (`generate_password_hash` / `check_password_hash`).
  - Route protections (`@login_required`) and brute-force attempt limits.
- **📋 Full Task Lifecycle Management (CRUD)**:
  - Add tasks with title, description, priority (`Low`, `Medium`, `High`), deadline, and custom reminder offsets.
  - Interactive cards with custom checkboxes, priority pills, and smart urgency tags (*Overdue*, *Due Today*, *Due Tomorrow*).
  - Pre-populated modal dialog for editing tasks.
  - Real-time debounced search and segmented filtering by Status and Priority.
- **📈 Personalized Learning & Progress Tracking**:
  - Real-time completion rates (overall and current week).
  - Motivational **Study Streak Counter** (`🔥 4-Day Streak`).
  - 7-Day Completion Velocity Chart (pure CSS/SVG).
  - Urgency breakdown showing pending tasks by priority.
  - Dynamic encouraging messages tailored to user performance.
- **📅 Interactive Monthly Calendar View**:
  - Full monthly calendar grid with previous/next month navigation and "Today" quick-jump.
  - Color-coded deadline dots on calendar days.
  - Click-to-inspect day drawer displaying all tasks scheduled for a selected date.
- **🔔 Task Reminders & Notifications**:
  - In-app notification bell with real-time badge count in the navbar.
  - Dropdown listing overdue and upcoming assignments.
  - Native Web Browser Notification API integration for desktop alert banners.
- **Modern Minimalist UI (Linear-Inspired)**:
  - Clean typography, electric indigo brand accent, smooth modal transitions, animated checkboxes, and mobile-friendly responsive layout.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Flask 3.0.3, Gunicorn 22.0.0, Werkzeug Security
- **Database**: SQLite3 (embedded relational database with foreign keys and performance indexes)
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
├── app.py                 # Flask app factory, auth routes, session management, and REST API
├── database.py            # SQLite database connection manager and schema migration helper
├── schema.sql             # Relational schema (users, tasks) with constraints and indexes
├── seed.py                # Database seeding script with demo student account and sample tasks
├── templates/
│   ├── login.html         # Modern student login page with password visibility toggle
│   ├── signup.html        # Student registration page with input validation
│   └── index.html         # Dashboard layout with view switcher (Tasks, Calendar, Progress)
├── static/
│   ├── css/
│   │   └── style.css      # Linear-inspired design system with CSS variables and responsive styles
│   └── js/
│       └── app.js         # Vanilla JavaScript handling views, calendar, progress, reminders, and CRUD
├── tests/
│   ├── __init__.py        # Test package marker
│   ├── conftest.py        # Pytest fixtures for authenticated client and temporary DB
│   └── test_api.py        # Comprehensive test suite covering auth, validation, progress, calendar, and reminders
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
Populate the SQLite database with the demo student account, sample coursework, and progress metrics:
```bash
python seed.py
```
> **Demo Account**: `demo@student.edu` / `Password123!`

### 5. Run the Application
```bash
python app.py
```
Open your browser and navigate to: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📡 REST API Reference

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/signup` | Public | Register new student account |
| `POST` | `/login` | Public | Authenticate user & start session |
| `GET` | `/logout` | Authenticated | End user session |
| `GET` | `/api/me` | Authenticated | Get current student profile |
| `GET` | `/api/tasks` | Authenticated | List all tasks (`?status=&priority=`) |
| `POST` | `/api/tasks` | Authenticated | Create a new task with reminder setting |
| `PUT` | `/api/tasks/<id>` | Authenticated | Update task details |
| `PATCH`| `/api/tasks/<id>/complete`| Authenticated | Toggle task completion |
| `DELETE`| `/api/tasks/<id>`| Authenticated | Delete task by ID |
| `GET` | `/api/tasks/search` | Authenticated | Search current user tasks (`?q=`) |
| `GET` | `/api/progress` | Authenticated | Get progress metrics, streaks, and chart history |
| `GET` | `/api/tasks/calendar` | Authenticated | Get tasks grouped by day (`?month=&year=`) |
| `GET` | `/api/reminders` | Authenticated | Get overdue and upcoming reminder items |

---

## 🧪 Testing

The test suite is built with `pytest` and covers auth validation, user isolation, task CRUD, progress analytics, calendar grouping, and reminder matching.

To run the test suite:
```bash
pytest -v
```

---

## 📸 Deliverable Screenshots

1. **Home/Dashboard – Student Task Manager main page**  
   <!-- ![Screenshot 1: Home/Dashboard](screenshots/01_dashboard.png) -->
   *Caption: Redesigned dashboard displaying header navbar with view switcher, stats metric strip, and task list feed.*

2. **Add Task – form for entering task title, priority, due date, and reminder**  
   <!-- ![Screenshot 2: Add Task](screenshots/02_add_task.png) -->
   *Caption: Unified modal window for adding new coursework with priority selector, deadline picker, and reminder offset.*

3. **Task List – display of all pending and completed tasks**  
   <!-- ![Screenshot 3: Task List](screenshots/03_task_list.png) -->
   *Caption: Main task feed rendering student tasks with custom checkboxes and color-coded priority badges.*

4. **Edit/Update Task – modified task details**  
   <!-- ![Screenshot 4: Edit/Update Task](screenshots/04_edit_task.png) -->
   *Caption: Interactive edit modal pre-filled with existing task data for inline modifications.*

5. **Task Completed – task marked as completed**  
   <!-- ![Screenshot 5: Task Completed](screenshots/05_completed_task.png) -->
   *Caption: Academic task marked as Completed with green status pill and strikethrough title styling.*

6. **Filter/Search – tasks filtered by priority or status**  
   <!-- ![Screenshot 6: Filter/Search](screenshots/06_filter_search.png) -->
   *Caption: Dashboard filtering tasks in real time by High Priority and keyword search.*

7. **Progress Analytics View – learning velocity and streaks**  
   <!-- ![Screenshot 7: Progress Analytics](screenshots/07_progress_analytics.png) -->
   *Caption: Personalized progress tracking view showing weekly completion gauge, streak flame, priority breakdown, and 7-day velocity chart.*

8. **Monthly Calendar View – visual deadline calendar**  
   <!-- ![Screenshot 8: Calendar View](screenshots/08_calendar_view.png) -->
   *Caption: Monthly calendar grid with color-coded task pills and interactive day inspector drawer.*

9. **Reminders & In-App Bell Dropdown – active notifications**  
   <!-- ![Screenshot 9: Reminders](screenshots/09_reminders.png) -->
   *Caption: In-app notification bell with active badge count and dropdown listing upcoming and overdue deadlines.*

10. **Database – SQLite database showing stored tasks and users**  
    <!-- ![Screenshot 10: Database](screenshots/10_database.png) -->
    *Caption: SQLite database tables (users and tasks) viewed in DB Browser for SQLite showing relational schema.*

11. **Testing Output – terminal showing successful pytest results**  
    <!-- ![Screenshot 11: Testing Output](screenshots/11_testing_output.png) -->
    *Caption: Terminal output demonstrating all automated pytest test cases passing.*

12. **Login & Sign Up Screens – student authentication**  
    <!-- ![Screenshot 12: Auth Screens](screenshots/12_auth_screens.png) -->
    *Caption: Clean student authentication login and registration screens with show/hide password toggle.*

---

## 👥 Author & Credits

- **Developer**: [Student Name Placeholder]
- **Technology Stack**: Python / Flask, SQLite, Vanilla HTML5 / CSS3 / JavaScript
- **AI Pair Programming Assistant**: Google DeepMind Antigravity / Claude Code
