# 🎓 Student Task Manager

> A lightweight, modern full-stack web application designed for students to organize, prioritize, track, and manage academic coursework, deadlines, and project milestones with secure multi-user authentication.

🔗 **Live Demo URL**: `https://student-task-manager-<your-subdomain>.onrender.com` *(or your deployed URL)*

---

## 📌 Problem Statement

College and high school students frequently juggle multiple simultaneous courses, lab assignments, project milestones, and exam dates. Without a centralized and lightweight tracking tool, deadlines are easily missed, and prioritizing urgent vs. low-priority coursework becomes overwhelming. Traditional productivity tools are often overly complex or bloated with unnecessary features.

The **Student Task Manager** solves this problem by providing a clean, responsive, distraction-free dashboard with personal student accounts where students can quickly create tasks, set priority levels, assign due dates, track progress in real-time, search instantly, and filter tasks without page reloads.

---

## 🔐 Authentication & Security

- **Multi-User Account System**: Secure student registration (`/signup`) and login (`/login`) with session management.
- **Strict Data Isolation**: Every task is linked to `user_id`; users only ever see, modify, search, or delete their own coursework.
- **Password Security**: Passwords are never stored in plain text; hashed using `werkzeug.security` (`generate_password_hash` / `check_password_hash`).
- **Protected REST API**: All `/api/tasks/*` routes require active authentication via `@login_required` decorator, returning `401 Unauthorized` for unauthenticated calls.
- **Brute-Force Login Protection**: In-memory rate-limiting and temporary lockout protection against credential-stuffing attacks.

---

## ✨ Features

- **Full Task Lifecycle Management (CRUD)**:
  - **Create**: Add tasks with title, description, priority (`Low`, `Medium`, `High`), and target due date via a sleek modal.
  - **Read**: View tasks neatly organized into interactive cards with color-coded priority and status badges.
  - **Update**: Edit existing tasks in place using a pre-populated modal dialog.
  - **Delete**: Remove tasks with safety confirmation prompts.
  - **Toggle Status**: Instantly mark tasks as `Completed` or `Pending` with a single checkbox toggle.
- **Live Summary Statistics**: Dynamic real-time counters displaying Total Coursework, Pending Tasks, Completed Tasks, and Overdue/Urgent tasks.
- **Real-Time Instant Search**: Live debounced search across titles and descriptions.
- **Multi-Criteria Filtering**: Instant filtering by Status (`All`, `Pending`, `Completed`) and Priority (`All`, `High`, `Medium`, `Low`), plus a one-click **Reset Filters** button.
- **Smart Due-Date Indicators**: Automatically flags tasks as *Overdue*, *Due Today*, or *Due Tomorrow*.
- **Modern Minimalist UI (Linear-Inspired)**: Clean typography, electric indigo brand accent, smooth modal transitions, animated checkboxes, and mobile-friendly responsive layout.
- **Toast Notifications**: Non-intrusive feedback toasts for every user action.

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
│   └── index.html         # Main dashboard layout with top navigation, stats strip, and task modal
├── static/
│   ├── css/
│   │   └── style.css      # Linear-inspired design system with CSS variables and responsive styles
│   └── js/
│       └── app.js         # Vanilla JavaScript handling API calls, live search, filters, and modal
├── tests/
│   ├── __init__.py        # Test package marker
│   ├── conftest.py        # Pytest fixtures for authenticated client and temporary DB
│   └── test_api.py        # Comprehensive test suite covering auth, validation, and task CRUD
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
Populate the SQLite database with the demo student account and sample coursework:
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

## 🌐 Free-Tier Cloud Deployment Guide (Render)

This application is fully production-configured with `gunicorn`, `Procfile`, and `runtime.txt` for one-click deployment on **Render** (Free Tier):

1. Push this `student-task-manager` repository to your **GitHub** account.
2. Sign up / Log in to [Render.com](https://render.com).
3. Click **New +** > **Web Service** and select your repository.
4. Set Build Command: `pip install -r requirements.txt` and Start Command: `gunicorn app:app`.
5. Select **Free** instance tier and click **Deploy Web Service**.

---

## 📡 REST API & Authentication Reference

| Method | Endpoint | Access | Description | Request Body / Query Params |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/login` | Public | Render login page | *None* |
| `POST`| `/login` | Public | Authenticate user & start session | `{"email": "...", "password": "..."}` |
| `GET` | `/signup` | Public | Render registration page | *None* |
| `POST`| `/signup` | Public | Register new user account | `{"name": "...", "email": "...", "password": "...", "confirm_password": "..."}` |
| `GET` | `/logout` | Authenticated | Destroy session | *None* |
| `GET` | `/api/me` | Authenticated | Get current student profile | *None* |
| `GET` | `/` | Authenticated | Render dashboard HTML page | *None* |
| `GET` | `/api/tasks` | Authenticated | List all tasks for current user | `?status=...&priority=...` |
| `GET` | `/api/tasks/<id>` | Authenticated | Get single task details | *None* |
| `POST`| `/api/tasks` | Authenticated | Create a new task | `{"title": "Math HW", "priority": "High", "due_date": "2026-09-20"}` |
| `PUT` | `/api/tasks/<id>` | Authenticated | Update existing task | `{"title": "Updated", "priority": "Low", "status": "Completed"}` |
| `PATCH`| `/api/tasks/<id>/complete`| Authenticated | Toggle task completion | `{"completed": true}` *(or empty body)* |
| `DELETE`| `/api/tasks/<id>`| Authenticated | Delete task by ID | *None* |
| `GET` | `/api/tasks/search` | Authenticated | Search current user tasks | `?q=search_term` |

---

## 📖 User Guide (For End Users)

1. **Sign Up or Log In**: Go to `/login` (use `demo@student.edu` / `Password123!` or create a new account at `/signup`).
2. **Adding a Task**: Click the **+ New Task** button in the top navbar. Enter title, description, priority, and due date in the modal, then click **Save Task**.
3. **Marking as Complete**: Click the custom checkbox on any task card. The task will update to `Completed` with a green badge and strikethrough styling.
4. **Editing a Task**: Click **✏️ Edit** on any card to open the modal with pre-populated details, modify fields, and click **Save Task**.
5. **Deleting a Task**: Click **🗑️ Delete** on the card and confirm the popup dialog.
6. **Searching & Filtering**: Use the search bar to filter by title/notes instantly, or click the **Status** (`Pending`, `Completed`) and **Priority** (`High`, `Med`, `Low`) segment buttons. Click **Reset Filters** to clear.
7. **Logging Out**: Click the **🚪 Logout** button in the top right user menu pill.

---

## 🧪 Testing

The test suite is built with `pytest` and covers registration, login/logout, route authentication protections, user data isolation, and task CRUD.

To run the test suite:
```bash
pytest -v
```

---

## 📸 Deliverable Screenshots

1. **Home/Dashboard – Student Task Manager main page**  
   <!-- ![Screenshot 1: Home/Dashboard](screenshots/01_dashboard.png) -->
   *Caption: Redesigned dashboard displaying header navbar with user pill, stats metric strip, and task list feed.*

2. **Add Task – form for entering task title, priority, and due date**  
   <!-- ![Screenshot 2: Add Task](screenshots/02_add_task.png) -->
   *Caption: Unified modal window for adding new coursework with priority selector and deadline picker.*

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

7. **Database – SQLite database showing stored tasks**  
   <!-- ![Screenshot 7: Database](screenshots/07_database.png) -->
   *Caption: SQLite database tables (users and tasks) viewed in DB Browser for SQLite showing relational schema.*

8. **Testing Output – terminal showing successful pytest results**  
   <!-- ![Screenshot 8: Testing Output](screenshots/08_testing_output.png) -->
   *Caption: Terminal output demonstrating 15 passing automated pytest test cases covering auth and task CRUD.*

9. **Login Screen – Student login page**  
   <!-- ![Screenshot 9: Login Screen](screenshots/09_login_screen.png) -->
   *Caption: Clean student authentication login page with show/hide password toggle and demo credentials.*

10. **Sign Up Screen – Student registration page**  
    <!-- ![Screenshot 10: Sign Up Screen](screenshots/10_signup_screen.png) -->
    *Caption: Student account registration screen with full name, academic email, and password validation.*

11. **Claude Code/Antigravity Interaction – AI assisting with implementation/debugging**  
    <!-- ![Screenshot 11: AI Interaction](screenshots/11_ai_interaction.png) -->
    *Caption: AI pair programming session assisting with auth architecture, UI redesign, and test automation.*

12. **Final Application – complete working application in the browser**  
    <!-- ![Screenshot 12: Final Application](screenshots/12_final_application.png) -->
    *Caption: Complete working Student Task Manager web application running with authenticated multi-user support.*

---

## 🔮 Future Improvements

1. **Email & Desktop Due-Date Reminders**: Automated notifications alerting students 24 hours prior to upcoming assignment deadlines.
2. **Course & Subject Categories**: Tagging tasks by academic course codes (e.g., `CS101`, `MATH202`) with color-coded subject groupings.
3. **Calendar View**: Visual monthly and weekly calendar views for upcoming deadlines.

---

## 👥 Author & Credits

- **Developer**: [Student Name Placeholder]
- **Technology Stack**: Python / Flask, SQLite, Vanilla HTML5 / CSS3 / JavaScript
- **AI Pair Programming Assistant**: Google DeepMind Antigravity / Claude Code
