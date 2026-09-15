/**
 * Student Task Manager - Frontend JavaScript
 * Handles Views (Tasks, Calendar, Progress), Theme Toggling, Loading Skeletons,
 * Micro-interactions, Reminders, Search, Filters, and Modal CRUD.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Global State
  let tasks = [];
  let currentView = "tasks";
  let activeStatusFilter = "";
  let activePriorityFilter = "";
  let searchQuery = "";
  let searchDebounceTimeout = null;

  // Calendar State
  const now = new Date();
  let currentCalMonth = now.getMonth() + 1; // 1-12
  let currentCalYear = now.getFullYear();
  let calendarData = {};
  let selectedCalDate = null;

  // DOM: General & Navigation
  const navTabButtons = document.querySelectorAll(".nav-tab-btn");
  const viewPanels = {
    tasks: document.getElementById("view-tasks"),
    calendar: document.getElementById("view-calendar"),
    progress: document.getElementById("view-progress")
  };
  const currentDateDisplay = document.getElementById("current-date-display");
  const dashboardViewTitle = document.getElementById("dashboard-view-title");
  const errorBanner = document.getElementById("error-banner");
  const errorBannerText = document.getElementById("error-banner-text");

  // DOM: Theme Toggle
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  const themeToggleIcon = document.getElementById("theme-toggle-icon");

  // DOM: Reminders
  const bellToggleBtn = document.getElementById("bell-toggle-btn");
  const reminderBadge = document.getElementById("reminder-badge");
  const remindersDropdown = document.getElementById("reminders-dropdown");
  const remindersList = document.getElementById("reminders-list");
  const btnRequestBrowserNotify = document.getElementById("btn-request-browser-notify");

  // DOM: Tasks Feed & Stats
  const tasksContainer = document.getElementById("tasks-container");
  const emptyState = document.getElementById("empty-state");
  const emptyStateAddBtn = document.getElementById("empty-state-add-btn");
  const searchInput = document.getElementById("search-input");
  const clearSearchBtn = document.getElementById("clear-search-btn");
  const resetFiltersBtn = document.getElementById("reset-filters-btn");
  const statusFilterButtons = document.querySelectorAll("#status-filters .segment-btn");
  const priorityFilterButtons = document.querySelectorAll("#priority-filters .segment-btn");

  // DOM: Calendar View
  const calPrevMonthBtn = document.getElementById("cal-prev-month-btn");
  const calNextMonthBtn = document.getElementById("cal-next-month-btn");
  const calTodayBtn = document.getElementById("cal-today-btn");
  const calMonthTitle = document.getElementById("cal-month-title");
  const calDaysGrid = document.getElementById("cal-days-grid");
  const inspectorSelectedDate = document.getElementById("inspector-selected-date");
  const inspectorCountBadge = document.getElementById("inspector-count-badge");
  const inspectorTasksList = document.getElementById("inspector-tasks-list");

  // DOM: Progress View
  const progressMotivationTitle = document.getElementById("progress-motivation-title");
  const progressMotivationText = document.getElementById("progress-motivation-text");
  const progressStreakCount = document.getElementById("progress-streak-count");
  const progressWeekFill = document.getElementById("progress-week-fill");
  const progressWeekRate = document.getElementById("progress-week-rate");
  const progressOverallFill = document.getElementById("progress-overall-fill");
  const progressOverallRate = document.getElementById("progress-overall-rate");
  const progressTasksRatio = document.getElementById("progress-tasks-ratio");
  const breakdownHigh = document.getElementById("breakdown-high");
  const breakdownMed = document.getElementById("breakdown-med");
  const breakdownLow = document.getElementById("breakdown-low");
  const activityChartContainer = document.getElementById("activity-chart-container");

  // DOM: Side Rail Analytics (2-Column Dashboard)
  const sideStreakCount = document.getElementById("side-streak-count");
  const sideMotivationText = document.getElementById("side-motivation-text");
  const sideWeekRate = document.getElementById("side-week-rate");
  const sideWeekFill = document.getElementById("side-week-fill");
  const sideTasksRatio = document.getElementById("side-tasks-ratio");
  const sideActivityChartContainer = document.getElementById("side-activity-chart-container");
  const sideBreakdownHigh = document.getElementById("side-breakdown-high");
  const sideBreakdownMed = document.getElementById("side-breakdown-med");
  const sideBreakdownLow = document.getElementById("side-breakdown-low");

  // DOM: Modal
  const taskModal = document.getElementById("task-modal");
  const taskForm = document.getElementById("task-form");
  const modalTitle = document.getElementById("modal-title");
  const formTaskId = document.getElementById("form-task-id");
  const formTitle = document.getElementById("form-task-title");
  const formDesc = document.getElementById("form-task-desc");
  const formPriority = document.getElementById("form-task-priority");
  const formDueDate = document.getElementById("form-task-due-date");
  const formReminder = document.getElementById("form-task-reminder");
  const formStatusGroup = document.getElementById("form-status-group");
  const formStatus = document.getElementById("form-task-status");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalCancelBtn = document.getElementById("modal-cancel-btn");
  const openNewTaskModalBtn = document.getElementById("open-new-task-modal-btn");

  // -----------------------------------------------------------------
  // 1. Theme Management (Light / Dark with System Fallback)
  // -----------------------------------------------------------------
  function initTheme() {
    const savedTheme = localStorage.getItem("stm_theme");
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initialTheme = savedTheme || (systemPrefersDark ? "dark" : "light");

    applyTheme(initialTheme);

    if (themeToggleBtn) {
      themeToggleBtn.addEventListener("click", () => {
        const current = document.documentElement.getAttribute("data-theme") || "dark";
        const next = current === "dark" ? "light" : "dark";
        applyTheme(next);
      });
    }

    // Listen for system theme changes if not overridden
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
      if (!localStorage.getItem("stm_theme")) {
        applyTheme(e.matches ? "dark" : "light");
      }
    });
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("stm_theme", theme);
    if (themeToggleIcon) {
      themeToggleIcon.textContent = theme === "light" ? "☀️" : "🌙";
    }
  }

  // -----------------------------------------------------------------
  // Initial Setup
  // -----------------------------------------------------------------
  function init() {
    initTheme();
    renderCurrentDate();
    showLoadingSkeletons();
    fetchTasksAndStats();
    fetchProgressAnalytics();
    fetchReminders();
    attachEventListeners();
  }

  function renderCurrentDate() {
    if (!currentDateDisplay) return;
    const day = now.getDate();
    const month = now.toLocaleDateString(undefined, { month: "short" });
    const year = now.getFullYear();
    currentDateDisplay.textContent = `${day} ${month} ${year}`;
  }

  function showLoadingSkeletons() {
    if (tasksContainer && tasks.length === 0) {
      tasksContainer.innerHTML = `
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>
        <div class="skeleton skeleton-card"></div>
      `;
    }
  }

  function showErrorBanner(msg = "Unable to load tasks") {
    if (errorBanner) {
      if (errorBannerText) errorBannerText.textContent = msg;
      errorBanner.style.display = "flex";
    }
  }

  function hideErrorBanner() {
    if (errorBanner) {
      errorBanner.style.display = "none";
    }
  }

  // -----------------------------------------------------------------
  // View Switcher (Tasks / Calendar / Progress)
  // -----------------------------------------------------------------
  function switchView(targetView) {
    currentView = targetView;

    navTabButtons.forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-view") === targetView);
    });

    Object.keys(viewPanels).forEach(key => {
      if (viewPanels[key]) {
        viewPanels[key].style.display = key === targetView ? "flex" : "none";
      }
    });

    if (dashboardViewTitle) {
      if (targetView === "tasks") dashboardViewTitle.textContent = "Daily Tasks";
      else if (targetView === "calendar") dashboardViewTitle.textContent = "Academic Calendar";
      else if (targetView === "progress") dashboardViewTitle.textContent = "Learning Analytics";
    }

    if (targetView === "tasks") {
      fetchTasksAndStats();
    } else if (targetView === "calendar") {
      fetchCalendarData(currentCalMonth, currentCalYear);
    } else if (targetView === "progress") {
      fetchProgressAnalytics();
    }
  }

  // -----------------------------------------------------------------
  // Toast Notifications (Deduplicated & Smooth Animation)
  // -----------------------------------------------------------------
  function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container || !message) return;

    // Prevent duplicate stacked toasts
    const existing = container.querySelectorAll(".toast");
    for (const t of existing) {
      if (t.getAttribute("data-message") === message) return;
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.setAttribute("data-message", message);
    const icon = type === "success" ? "✓" : "⚠️";
    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(12px) scale(0.95)";
      setTimeout(() => toast.remove(), 250);
    }, 3200);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatDueDate(dateString) {
    if (!dateString) return { text: "", className: "" };

    const due = new Date(dateString + "T00:00:00");
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const diffTime = due.getTime() - today.getTime();
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return { text: `Overdue (${dateString})`, className: "due-overdue" };
    } else if (diffDays === 0) {
      return { text: "Due Today", className: "due-today" };
    } else if (diffDays === 1) {
      return { text: "Due Tomorrow", className: "due-today" };
    } else {
      const options = { month: "short", day: "numeric" };
      return { text: `Due ${due.toLocaleDateString(undefined, options)}`, className: "" };
    }
  }

  // -----------------------------------------------------------------
  // 2. TASKS FEED VIEW
  // -----------------------------------------------------------------
  async function fetchTasksAndStats() {
    try {
      const res = await fetch("/api/tasks");
      if (res.status === 401) {
        window.location.href = "/login";
        return;
      }
      if (!res.ok) throw new Error("Failed to load tasks");
      const allTasks = await res.json();
      tasks = allTasks;
      hideErrorBanner();
      applyCurrentFilters();
    } catch (err) {
      console.error("fetchTasksAndStats error:", err);
      showErrorBanner("Unable to load tasks");
    }
  }

  async function applyCurrentFilters() {
    let displayedTasks = tasks;

    if (searchQuery.trim()) {
      try {
        const res = await fetch(`/api/tasks/search?q=${encodeURIComponent(searchQuery.trim())}`);
        if (res.status === 401) {
          window.location.href = "/login";
          return;
        }
        if (res.ok) {
          displayedTasks = await res.json();
        }
      } catch (e) {
        console.error("Search error", e);
      }
    }

    if (activeStatusFilter) {
      displayedTasks = displayedTasks.filter(t => t.status === activeStatusFilter);
    }
    if (activePriorityFilter) {
      displayedTasks = displayedTasks.filter(t => t.priority === activePriorityFilter);
    }

    renderTasks(displayedTasks);
  }

  function renderTasks(taskList) {
    if (!tasksContainer) return;
    tasksContainer.innerHTML = "";

    if (taskList.length === 0) {
      if (emptyState) emptyState.style.display = "flex";
      return;
    }
    if (emptyState) emptyState.style.display = "none";

    taskList.forEach((task, index) => {
      const card = document.createElement("div");
      card.className = `task-card ${task.status === "Completed" ? "is-completed" : ""}`;
      card.setAttribute("data-id", task.id);
      card.style.animationDelay = `${Math.min(index * 35, 300)}ms`;

      const dueInfo = formatDueDate(task.due_date);
      const isCompleted = task.status === "Completed";
      const priorityClass = `priority-${task.priority.toLowerCase()}`;

      // Course code regex extraction (e.g. CS201, CS-101, [MATH302], EE200)
      const courseMatch = task.title.match(/^(\[?([A-Z]{2,5}\s?-?\d{2,4})\]?:?\s*)/i);
      let displayTitle = task.title;
      let courseTagHtml = "";
      if (courseMatch) {
        const fullMatchedPrefix = courseMatch[1];
        const rawCode = courseMatch[2].toUpperCase().replace(/\s+/, "");
        courseTagHtml = `<span class="course-tag">${escapeHtml(rawCode)}</span>`;
        displayTitle = task.title.slice(fullMatchedPrefix.length) || task.title;
      }

      card.innerHTML = `
        <div class="task-card-header">
          <label class="task-checkbox-label" title="Mark as ${isCompleted ? 'pending' : 'completed'}">
            <input type="checkbox" class="task-custom-checkbox" ${isCompleted ? "checked" : ""}>
          </label>
          <div class="task-card-main-col">
            <div class="task-card-title-row">
              <div class="task-title-group">
                ${courseTagHtml}
                <h4 class="task-title">${escapeHtml(displayTitle)}</h4>
              </div>
              <div class="task-priority-indicator ${priorityClass}">
                <span class="priority-dot dot-${task.priority.toLowerCase()}"></span>
                <span>${escapeHtml(task.priority)}</span>
              </div>
            </div>
            ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ""}
            <div class="task-card-footer">
              ${dueInfo.text ? `<div class="task-due-tag ${dueInfo.className}"><span>📅 ${escapeHtml(dueInfo.text)}</span></div>` : `<div></div>`}
              <div class="task-card-actions">
                <button type="button" class="btn-action edit-task-btn" title="Edit task">Edit</button>
                <button type="button" class="btn-action btn-action-danger delete-task-btn" title="Delete task">Delete</button>
              </div>
            </div>
          </div>
        </div>
      `;

      // Checkbox event with tactile micro-animation
      const checkbox = card.querySelector(".task-custom-checkbox");
      checkbox.addEventListener("change", () => toggleComplete(task.id, checkbox.checked));

      // Edit event
      const editBtn = card.querySelector(".edit-task-btn");
      editBtn.addEventListener("click", () => openTaskModal(task));

      // Delete event
      const deleteBtn = card.querySelector(".delete-task-btn");
      deleteBtn.addEventListener("click", () => deleteTask(task.id, task.title));

      tasksContainer.appendChild(card);
    });
  }

  // -----------------------------------------------------------------
  // 3. CALENDAR VIEW
  // -----------------------------------------------------------------
  async function fetchCalendarData(month, year) {
    try {
      const res = await fetch(`/api/tasks/calendar?month=${month}&year=${year}`);
      if (res.status === 401) { window.location.href = "/login"; return; }
      if (!res.ok) throw new Error("Failed to load calendar data");

      const data = await res.json();
      calendarData = data.days || {};
      calMonthTitle.textContent = `${data.month_name} ${data.year}`;

      renderCalendarGrid(month, year);
    } catch (err) {
      console.error("Calendar error", err);
      showToast("Could not load calendar", "error");
    }
  }

  function renderCalendarGrid(month, year) {
    calDaysGrid.innerHTML = "";

    const firstDayIndex = new Date(year, month - 1, 1).getDay(); // 0 = Sun
    const totalDaysInMonth = new Date(year, month, 0).getDate();
    const prevMonthDays = new Date(year, month - 1, 0).getDate();

    const todayStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;

    // Previous month leading days
    for (let i = firstDayIndex - 1; i >= 0; i--) {
      const dayNum = prevMonthDays - i;
      const cell = document.createElement("div");
      cell.className = "cal-day-cell is-other-month";
      cell.innerHTML = `<span class="cal-day-num">${dayNum}</span>`;
      calDaysGrid.appendChild(cell);
    }

    // Current month days
    for (let day = 1; day <= totalDaysInMonth; day++) {
      const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
      const dayTasks = calendarData[dateStr] || [];

      const cell = document.createElement("div");
      cell.className = "cal-day-cell";
      if (dateStr === todayStr) cell.classList.add("is-today");
      if (selectedCalDate === dateStr) cell.classList.add("is-selected");

      let taskPillsHtml = "";
      dayTasks.slice(0, 3).forEach(t => {
        const pClass = t.status === "Completed" ? "completed" : t.priority.toLowerCase();
        taskPillsHtml += `<div class="cal-task-pill ${pClass}">${escapeHtml(t.title)}</div>`;
      });
      if (dayTasks.length > 3) {
        taskPillsHtml += `<div class="cal-task-pill">+${dayTasks.length - 3} more</div>`;
      }

      cell.innerHTML = `
        <span class="cal-day-num">${day}</span>
        <div class="cal-day-dots">${taskPillsHtml}</div>
      `;

      cell.addEventListener("click", () => {
        document.querySelectorAll(".cal-day-cell").forEach(c => c.classList.remove("is-selected"));
        cell.classList.add("is-selected");
        selectedCalDate = dateStr;
        inspectCalendarDay(dateStr, dayTasks);
      });

      calDaysGrid.appendChild(cell);
    }

    // Auto-inspect selected date or today
    if (selectedCalDate && calendarData[selectedCalDate]) {
      inspectCalendarDay(selectedCalDate, calendarData[selectedCalDate]);
    } else if (calendarData[todayStr]) {
      inspectCalendarDay(todayStr, calendarData[todayStr]);
    }
  }

  function inspectCalendarDay(dateStr, dayTasks) {
    const formattedDate = new Date(dateStr + "T00:00:00").toLocaleDateString(undefined, {
      weekday: "short", month: "short", day: "numeric", year: "numeric"
    });
    inspectorSelectedDate.textContent = formattedDate;
    inspectorCountBadge.textContent = `${dayTasks.length} ${dayTasks.length === 1 ? "task" : "tasks"}`;

    if (dayTasks.length === 0) {
      inspectorTasksList.innerHTML = `<p class="inspector-empty-note">No assignments or deadlines scheduled for this date.</p>`;
      return;
    }

    inspectorTasksList.innerHTML = "";
    dayTasks.forEach(task => {
      const item = document.createElement("div");
      item.className = `task-card ${task.status === "Completed" ? "is-completed" : ""}`;
      item.innerHTML = `
        <div class="task-card-header">
          <label class="task-checkbox-label">
            <input type="checkbox" class="task-custom-checkbox" ${task.status === "Completed" ? "checked" : ""}>
          </label>
          <div class="task-card-main-col">
            <span class="task-title" style="font-size:0.88rem;">${escapeHtml(task.title)}</span>
            <div class="task-card-footer">
              <span class="task-priority-indicator priority-${task.priority.toLowerCase()}">
                <span class="priority-dot dot-${task.priority.toLowerCase()}"></span>
                ${escapeHtml(task.priority)}
              </span>
            </div>
          </div>
        </div>
      `;

      const cb = item.querySelector(".task-custom-checkbox");
      cb.addEventListener("change", async () => {
        await toggleComplete(task.id, cb.checked);
        fetchCalendarData(currentCalMonth, currentCalYear);
      });

      inspectorTasksList.appendChild(item);
    });
  }

  // -----------------------------------------------------------------
  // 4. PROGRESS & LEARNING ANALYTICS VIEW
  // -----------------------------------------------------------------
  async function fetchProgressAnalytics() {
    try {
      const res = await fetch("/api/progress");
      if (res.status === 401) { window.location.href = "/login"; return; }
      if (!res.ok) throw new Error("Failed to load progress stats");

      const data = await res.json();
      renderProgressView(data);
    } catch (err) {
      console.error("Progress fetch error", err);
      showToast("Could not load progress analytics", "error");
    }
  }

  function renderProgressView(data) {
    // 1. Full Progress View
    if (progressMotivationTitle) progressMotivationTitle.textContent = data.motivational_message;
    if (progressStreakCount) progressStreakCount.textContent = data.current_streak_days;
    if (progressWeekRate) progressWeekRate.textContent = `${data.completion_rate_week}%`;
    if (progressWeekFill) progressWeekFill.style.width = `${Math.min(100, Math.max(0, data.completion_rate_week))}%`;
    if (progressOverallRate) progressOverallRate.textContent = `${data.completion_rate_overall}%`;
    if (progressOverallFill) progressOverallFill.style.width = `${Math.min(100, Math.max(0, data.completion_rate_overall))}%`;
    if (progressTasksRatio) progressTasksRatio.textContent = `${data.completed_tasks} of ${data.total_tasks} tasks completed`;
    if (breakdownHigh) breakdownHigh.textContent = `${data.priority_breakdown.High || 0} High`;
    if (breakdownMed) breakdownMed.textContent = `${data.priority_breakdown.Medium || 0} Med`;
    if (breakdownLow) breakdownLow.textContent = `${data.priority_breakdown.Low || 0} Low`;

    // 2. Side Rail Analytics (2-Column Dashboard)
    if (sideStreakCount) sideStreakCount.textContent = `${data.current_streak_days} ${data.current_streak_days === 1 ? "Day" : "Days"}`;
    if (sideMotivationText) sideMotivationText.textContent = data.motivational_message;
    if (sideWeekRate) sideWeekRate.textContent = `${data.completion_rate_week}%`;
    if (sideWeekFill) sideWeekFill.style.width = `${Math.min(100, Math.max(0, data.completion_rate_week))}%`;
    if (sideTasksRatio) sideTasksRatio.textContent = `${data.completed_tasks} of ${data.total_tasks} tasks completed`;
    if (sideBreakdownHigh) sideBreakdownHigh.textContent = `${data.priority_breakdown.High || 0} High`;
    if (sideBreakdownMed) sideBreakdownMed.textContent = `${data.priority_breakdown.Medium || 0} Med`;
    if (sideBreakdownLow) sideBreakdownLow.textContent = `${data.priority_breakdown.Low || 0} Low`;

    // 3. Velocity Charts (Full view and Side rail)
    renderActivityChart(data.daily_completion_history || []);
  }

  function renderActivityChart(history) {
    const containers = [activityChartContainer, sideActivityChartContainer].filter(Boolean);
    containers.forEach(container => {
      container.innerHTML = "";
    });

    if (history.length === 0) return;
    const maxCount = Math.max(1, ...history.map(h => h.count));

    containers.forEach(container => {
      history.forEach(day => {
        const col = document.createElement("div");
        col.className = "chart-col";

        const heightPercent = Math.round((day.count / maxCount) * 100);
        const displayHeight = day.count > 0 ? Math.max(20, heightPercent) : 6;

        col.innerHTML = `
          <span class="chart-col-count">${day.count}</span>
          <div class="chart-bar-wrap" title="${day.count} tasks completed on ${day.date}">
            <div class="chart-bar-fill" style="height: ${displayHeight}%;"></div>
          </div>
          <span class="chart-col-label">${escapeHtml(day.day_name)}</span>
        `;
        container.appendChild(col);
      });
    });
  }

  // -----------------------------------------------------------------
  // 5. REMINDERS SYSTEM
  // -----------------------------------------------------------------
  async function fetchReminders() {
    try {
      const res = await fetch("/api/reminders");
      if (!res.ok) return;
      const data = await res.json();
      const count = data.count || 0;

      if (count > 0) {
        reminderBadge.textContent = count;
        reminderBadge.style.display = "flex";
      } else {
        reminderBadge.style.display = "none";
      }

      renderRemindersDropdown(data.reminders || []);
    } catch (e) {
      console.error("Reminders error", e);
    }
  }

  function renderRemindersDropdown(reminderItems) {
    remindersList.innerHTML = "";
    if (reminderItems.length === 0) {
      remindersList.innerHTML = `<p class="reminder-empty-note">🎉 No overdue or immediate deadlines right now!</p>`;
      return;
    }

    reminderItems.forEach(item => {
      const el = document.createElement("div");
      el.className = "reminder-item";
      el.innerHTML = `
        <span class="reminder-item-title">${escapeHtml(item.title)}</span>
        <div class="reminder-item-meta">
          <span class="reminder-reason-tag">${escapeHtml(item.reminder_reason)}</span>
          <span class="task-priority-indicator priority-${item.priority.toLowerCase()}">
            <span class="priority-dot dot-${item.priority.toLowerCase()}"></span>
            ${escapeHtml(item.priority)}
          </span>
        </div>
      `;
      el.addEventListener("click", () => {
        remindersDropdown.style.display = "none";
        openTaskModal(item);
      });
      remindersList.appendChild(el);
    });
  }

  if (btnRequestBrowserNotify) {
    btnRequestBrowserNotify.addEventListener("click", () => {
      if (!("Notification" in window)) {
        showToast("Browser does not support notifications", "error");
        return;
      }
      Notification.requestPermission().then(permission => {
        if (permission === "granted") {
          showToast("Desktop alerts enabled!", "success");
          new Notification("Student Task Manager", {
            body: "You will now receive notifications for upcoming coursework deadlines.",
            icon: "🎓"
          });
        }
      });
    });
  }

  // -----------------------------------------------------------------
  // 6. MODAL MANAGEMENT (Add / Edit Task)
  // -----------------------------------------------------------------
  function openTaskModal(task = null) {
    taskForm.reset();
    if (task) {
      modalTitle.textContent = "Edit Task";
      formTaskId.value = task.id;
      formTitle.value = task.title;
      formDesc.value = task.description || "";
      formPriority.value = task.priority;
      formDueDate.value = task.due_date || "";
      formReminder.value = task.reminder_offset || "none";
      formStatus.value = task.status;
      formStatusGroup.style.display = "block";
    } else {
      modalTitle.textContent = "Add New Task";
      formTaskId.value = "";
      formPriority.value = "Medium";
      formReminder.value = "none";
      formStatusGroup.style.display = "none";
    }
    taskModal.style.display = "flex";
    formTitle.focus();
  }

  function closeTaskModal() {
    taskModal.style.display = "none";
  }

  let isSubmittingTask = false;

  taskForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (isSubmittingTask) return;

    const taskId = formTaskId.value;
    const title = formTitle.value.trim();
    const description = formDesc.value.trim();
    const priority = formPriority.value;
    const due_date = formDueDate.value || null;
    const reminder_offset = formReminder.value || "none";
    const status = formStatusGroup.style.display === "none" ? "Pending" : formStatus.value;

    if (!title) {
      showToast("Title is required", "error");
      return;
    }

    const submitBtn = document.getElementById("modal-submit-btn");
    try {
      isSubmittingTask = true;
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = "Saving...";
      }

      let response;
      if (taskId) {
        response = await fetch(`/api/tasks/${taskId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, description, priority, due_date, status, reminder_offset })
        });
      } else {
        response = await fetch("/api/tasks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, description, priority, due_date, status: "Pending", reminder_offset })
        });
      }

      if (response.status === 401) {
        window.location.href = "/login";
        return;
      }

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to save task");

      showToast(taskId ? "Task updated successfully!" : "Task created successfully!", "success");
      closeTaskModal();

      // Refresh data
      fetchTasksAndStats();
      fetchProgressAnalytics();
      fetchReminders();
      if (currentView === "calendar") fetchCalendarData(currentCalMonth, currentCalYear);
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      isSubmittingTask = false;
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Save Task";
      }
    }
  });

  // -----------------------------------------------------------------
  // 7. ACTIONS: Complete & Delete
  // -----------------------------------------------------------------
  async function toggleComplete(taskId, isChecked) {
    try {
      const response = await fetch(`/api/tasks/${taskId}/complete`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ completed: isChecked })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to update status");

      showToast(data.message, "success");
      fetchTasksAndStats();
      fetchProgressAnalytics();
      fetchReminders();
      if (currentView === "calendar") fetchCalendarData(currentCalMonth, currentCalYear);
    } catch (err) {
      showToast(err.message, "error");
      fetchTasksAndStats();
    }
  }

  async function deleteTask(taskId, taskTitle) {
    const confirmed = window.confirm(`Are you sure you want to delete "${taskTitle}"?`);
    if (!confirmed) return;

    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: "DELETE"
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to delete task");

      showToast("Task deleted successfully", "success");
      fetchTasksAndStats();
      fetchProgressAnalytics();
      fetchReminders();
      if (currentView === "calendar") fetchCalendarData(currentCalMonth, currentCalYear);
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  // -----------------------------------------------------------------
  // 8. EVENT LISTENERS
  // -----------------------------------------------------------------
  function attachEventListeners() {
    // Navigation Tabs
    navTabButtons.forEach(btn => {
      btn.addEventListener("click", () => switchView(btn.getAttribute("data-view")));
    });

    // Reminders Bell Dropdown Toggle
    if (bellToggleBtn) {
      bellToggleBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        remindersDropdown.style.display = remindersDropdown.style.display === "none" ? "block" : "none";
      });
    }

    document.addEventListener("click", (e) => {
      if (remindersDropdown && !remindersDropdown.contains(e.target) && e.target !== bellToggleBtn) {
        remindersDropdown.style.display = "none";
      }
    });

    // Calendar Navigation
    if (calPrevMonthBtn) {
      calPrevMonthBtn.addEventListener("click", () => {
        currentCalMonth--;
        if (currentCalMonth < 1) { currentCalMonth = 12; currentCalYear--; }
        fetchCalendarData(currentCalMonth, currentCalYear);
      });
    }

    if (calNextMonthBtn) {
      calNextMonthBtn.addEventListener("click", () => {
        currentCalMonth++;
        if (currentCalMonth > 12) { currentCalMonth = 1; currentCalYear++; }
        fetchCalendarData(currentCalMonth, currentCalYear);
      });
    }

    if (calTodayBtn) {
      calTodayBtn.addEventListener("click", () => {
        currentCalMonth = now.getMonth() + 1;
        currentCalYear = now.getFullYear();
        fetchCalendarData(currentCalMonth, currentCalYear);
      });
    }

    // Modal Triggers
    if (openNewTaskModalBtn) openNewTaskModalBtn.addEventListener("click", () => openTaskModal(null));
    if (emptyStateAddBtn) emptyStateAddBtn.addEventListener("click", () => openTaskModal(null));
    if (modalCloseBtn) modalCloseBtn.addEventListener("click", closeTaskModal);
    if (modalCancelBtn) modalCancelBtn.addEventListener("click", closeTaskModal);
    if (taskModal) {
      taskModal.addEventListener("click", (e) => {
        if (e.target === taskModal) closeTaskModal();
      });
    }

    // Debounced Search
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value;
        if (clearSearchBtn) clearSearchBtn.style.display = searchQuery ? "inline-block" : "none";

        clearTimeout(searchDebounceTimeout);
        searchDebounceTimeout = setTimeout(() => {
          applyCurrentFilters();
        }, 200);
      });
    }

    if (clearSearchBtn) {
      clearSearchBtn.addEventListener("click", () => {
        searchInput.value = "";
        searchQuery = "";
        clearSearchBtn.style.display = "none";
        applyCurrentFilters();
      });
    }

    // Status Filter Segment
    statusFilterButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        statusFilterButtons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        activeStatusFilter = btn.getAttribute("data-status");
        applyCurrentFilters();
      });
    });

    // Priority Filter Segment
    priorityFilterButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        priorityFilterButtons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        activePriorityFilter = btn.getAttribute("data-priority");
        applyCurrentFilters();
      });
    });

    // Reset Filters
    if (resetFiltersBtn) {
      resetFiltersBtn.addEventListener("click", () => {
        searchQuery = "";
        if (searchInput) searchInput.value = "";
        if (clearSearchBtn) clearSearchBtn.style.display = "none";

        activeStatusFilter = "";
        statusFilterButtons.forEach(b => b.classList.toggle("active", b.getAttribute("data-status") === ""));

        activePriorityFilter = "";
        priorityFilterButtons.forEach(b => b.classList.toggle("active", b.getAttribute("data-priority") === ""));

        applyCurrentFilters();
      });
    }

    // Global Keyboard Shortcuts (⌘K, /, Escape, N)
    document.addEventListener("keydown", (e) => {
      const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
      const isInputActive = activeTag === "input" || activeTag === "textarea" || activeTag === "select";

      // ⌘K, Ctrl+K, or '/' to focus search
      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || (e.key === "/" && !isInputActive)) {
        e.preventDefault();
        if (searchInput) {
          searchInput.focus();
          searchInput.select();
        }
      }

      // Escape to blur search or close modal
      if (e.key === "Escape") {
        if (taskModal && taskModal.style.display !== "none") {
          closeTaskModal();
        } else if (document.activeElement === searchInput) {
          searchInput.blur();
        }
      }

      // 'n' or 'N' to open New Task modal (when not typing in an input)
      if ((e.key === "n" || e.key === "N") && !isInputActive && !(e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        openTaskModal(null);
      }
    });
  }

  init();
});
