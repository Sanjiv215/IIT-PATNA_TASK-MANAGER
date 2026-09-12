/**
 * Student Task Manager - Frontend JavaScript
 * Handles Views (Tasks, Calendar, Progress), Reminders, Search, Filters, and Modal CRUD.
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
  const visibleCountBadge = document.getElementById("visible-count");
  const statTotal = document.getElementById("stat-total");
  const statPending = document.getElementById("stat-pending");
  const statCompleted = document.getElementById("stat-completed");
  const statOverdue = document.getElementById("stat-overdue");
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
  const quickAddBtn = document.getElementById("btn-quick-add");

  // -----------------------------------------------------------------
  // Initial Setup
  // -----------------------------------------------------------------
  function init() {
    renderCurrentDate();
    fetchTasksAndStats();
    fetchReminders();
    attachEventListeners();
  }

  function renderCurrentDate() {
    if (!currentDateDisplay) return;
    const options = { weekday: "short", month: "short", day: "numeric", year: "numeric" };
    currentDateDisplay.textContent = `📅 ${now.toLocaleDateString(undefined, options)}`;
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

    if (targetView === "tasks") {
      fetchTasksAndStats();
    } else if (targetView === "calendar") {
      fetchCalendarData(currentCalMonth, currentCalYear);
    } else if (targetView === "progress") {
      fetchProgressAnalytics();
    }
  }

  // -----------------------------------------------------------------
  // Toast Notifications
  // -----------------------------------------------------------------
  function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "✓" : "⚠️";
    toast.innerHTML = `<span>${icon}</span> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      setTimeout(() => toast.remove(), 250);
    }, 3000);
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
    if (!dateString) return { text: "No deadline", className: "" };

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
  // 1. TASKS FEED VIEW
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
      renderStats(allTasks);
      applyCurrentFilters();
    } catch (err) {
      console.error(err);
      showToast("Could not load tasks from server", "error");
    }
  }

  function renderStats(allTasks) {
    const total = allTasks.length;
    const completed = allTasks.filter(t => t.status === "Completed").length;
    const pending = total - completed;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const overdueCount = allTasks.filter(t => {
      if (t.status === "Completed" || !t.due_date) return false;
      const due = new Date(t.due_date + "T00:00:00");
      return due.getTime() < today.getTime();
    }).length;

    if (statTotal) statTotal.textContent = total;
    if (statPending) statPending.textContent = pending;
    if (statCompleted) statCompleted.textContent = completed;
    if (statOverdue) statOverdue.textContent = overdueCount;
  }

  async function applyCurrentFilters() {
    let displayedTasks = tasks;

    if (searchQuery.trim()) {
      try {
        const res = await fetch(`/api/tasks/search?q=${encodeURIComponent(searchQuery.trim())}`);
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
    tasksContainer.innerHTML = "";
    visibleCountBadge.textContent = `${taskList.length} ${taskList.length === 1 ? "task" : "tasks"}`;

    if (taskList.length === 0) {
      emptyState.style.display = "block";
      return;
    }
    emptyState.style.display = "none";

    taskList.forEach(task => {
      const card = document.createElement("div");
      card.className = `task-card ${task.status === "Completed" ? "is-completed" : ""}`;
      card.setAttribute("data-id", task.id);

      const dueInfo = formatDueDate(task.due_date);
      const isCompleted = task.status === "Completed";
      const priorityClass = `badge-${task.priority.toLowerCase()}`;
      const statusClass = `badge-${task.status.toLowerCase()}`;

      card.innerHTML = `
        <div class="task-card-header">
          <div class="task-checkbox-title">
            <input type="checkbox" class="task-custom-checkbox" ${isCompleted ? "checked" : ""} title="Mark complete/pending">
            <h4 class="task-title">${escapeHtml(task.title)}</h4>
          </div>
          <div class="task-badges">
            <span class="badge ${priorityClass}">${escapeHtml(task.priority)}</span>
            <span class="badge ${statusClass}">${escapeHtml(task.status)}</span>
          </div>
        </div>

        ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ""}

        <div class="task-card-footer">
          <div class="task-due-tag ${dueInfo.className}">
            <span>🗓️</span> <span>${escapeHtml(dueInfo.text)}</span>
          </div>
          <div class="task-card-actions">
            <button class="btn btn-secondary btn-sm edit-task-btn" title="Edit task">✏️ Edit</button>
            <button class="btn btn-danger btn-sm delete-task-btn" title="Delete task">🗑️ Delete</button>
          </div>
        </div>
      `;

      // Checkbox event
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
  // 2. CALENDAR VIEW
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

    // Auto-inspect today or selected date
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
      item.className = "task-card";
      item.innerHTML = `
        <div class="task-card-header">
          <div class="task-checkbox-title">
            <input type="checkbox" class="task-custom-checkbox" ${task.status === "Completed" ? "checked" : ""}>
            <span class="task-title" style="font-size:0.88rem;">${escapeHtml(task.title)}</span>
          </div>
          <span class="badge badge-${task.priority.toLowerCase()}">${escapeHtml(task.priority)}</span>
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
  // 3. PROGRESS & LEARNING ANALYTICS VIEW
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
    // Motivational Message & Streak
    progressMotivationTitle.textContent = data.motivational_message;
    progressStreakCount.textContent = data.current_streak_days;

    // Progress Bars
    progressWeekRate.textContent = `${data.completion_rate_week}%`;
    progressWeekFill.style.width = `${Math.min(100, Math.max(0, data.completion_rate_week))}%`;

    progressOverallRate.textContent = `${data.completion_rate_overall}%`;
    progressOverallFill.style.width = `${Math.min(100, Math.max(0, data.completion_rate_overall))}%`;
    progressTasksRatio.textContent = `${data.completed_tasks} of ${data.total_tasks} tasks completed`;

    // Priority Breakdown
    breakdownHigh.textContent = `${data.priority_breakdown.High || 0} High`;
    breakdownMed.textContent = `${data.priority_breakdown.Medium || 0} Med`;
    breakdownLow.textContent = `${data.priority_breakdown.Low || 0} Low`;

    // 7-Day Velocity Chart
    renderActivityChart(data.daily_completion_history || []);
  }

  function renderActivityChart(history) {
    activityChartContainer.innerHTML = "";
    if (history.length === 0) return;

    const maxCount = Math.max(1, ...history.map(h => h.count));

    history.forEach(day => {
      const col = document.createElement("div");
      col.className = "chart-col";

      const heightPercent = Math.round((day.count / maxCount) * 100);
      const displayHeight = day.count > 0 ? Math.max(15, heightPercent) : 4;

      col.innerHTML = `
        <span class="chart-col-count">${day.count}</span>
        <div class="chart-bar-wrap">
          <div class="chart-bar-fill" style="height: ${displayHeight}%;"></div>
        </div>
        <span class="chart-col-label">${escapeHtml(day.day_name)}</span>
      `;
      activityChartContainer.appendChild(col);
    });
  }

  // -----------------------------------------------------------------
  // 4. REMINDERS SYSTEM
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
          <span class="badge badge-${item.priority.toLowerCase()}">${escapeHtml(item.priority)}</span>
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
            body: "You will now receive desktop notifications for upcoming coursework deadlines.",
            icon: "🎓"
          });
        }
      });
    });
  }

  // -----------------------------------------------------------------
  // 5. MODAL MANAGEMENT (Add / Edit Task)
  // -----------------------------------------------------------------
  function openTaskModal(task = null) {
    taskForm.reset();
    if (task) {
      modalTitle.textContent = "✏️ Edit Task";
      formTaskId.value = task.id;
      formTitle.value = task.title;
      formDesc.value = task.description || "";
      formPriority.value = task.priority;
      formDueDate.value = task.due_date || "";
      formReminder.value = task.reminder_offset || "none";
      formStatus.value = task.status;
      formStatusGroup.style.display = "block";
    } else {
      modalTitle.textContent = "➕ Add New Task";
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

  taskForm.addEventListener("submit", async (e) => {
    e.preventDefault();
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

    try {
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

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to save task");

      showToast(taskId ? "Task updated successfully!" : "Task added successfully!", "success");
      closeTaskModal();

      // Refresh current view & reminders
      fetchTasksAndStats();
      fetchReminders();
      if (currentView === "calendar") fetchCalendarData(currentCalMonth, currentCalYear);
      if (currentView === "progress") fetchProgressAnalytics();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // -----------------------------------------------------------------
  // 6. ACTIONS: Complete & Delete
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
      fetchReminders();
      if (currentView === "calendar") fetchCalendarData(currentCalMonth, currentCalYear);
      if (currentView === "progress") fetchProgressAnalytics();
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
      fetchReminders();
      if (currentView === "calendar") fetchCalendarData(currentCalMonth, currentCalYear);
      if (currentView === "progress") fetchProgressAnalytics();
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  // -----------------------------------------------------------------
  // 7. EVENT LISTENERS
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
    if (quickAddBtn) quickAddBtn.addEventListener("click", () => openTaskModal(null));
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
        }, 250);
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
  }

  init();
});
