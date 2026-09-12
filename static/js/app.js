/**
 * Student Task Manager - Frontend JavaScript
 * Handles REST API interactions, dynamic DOM updates, filtering, searching, and modals.
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let tasks = [];
  let activeStatusFilter = "";
  let activePriorityFilter = "";
  let searchQuery = "";
  let searchDebounceTimeout = null;

  // DOM Elements
  const tasksContainer = document.getElementById("tasks-container");
  const emptyState = document.getElementById("empty-state");
  const emptyStateAddBtn = document.getElementById("empty-state-add-btn");
  const visibleCountBadge = document.getElementById("visible-count");
  const currentDateDisplay = document.getElementById("current-date-display");

  // Stats DOM
  const statTotal = document.getElementById("stat-total");
  const statPending = document.getElementById("stat-pending");
  const statCompleted = document.getElementById("stat-completed");
  const statOverdue = document.getElementById("stat-overdue");

  // Search & Filter DOM
  const searchInput = document.getElementById("search-input");
  const clearSearchBtn = document.getElementById("clear-search-btn");
  const resetFiltersBtn = document.getElementById("reset-filters-btn");
  const statusFilterButtons = document.querySelectorAll("#status-filters .segment-btn");
  const priorityFilterButtons = document.querySelectorAll("#priority-filters .segment-btn");

  // Modal DOM
  const taskModal = document.getElementById("task-modal");
  const taskForm = document.getElementById("task-form");
  const modalTitle = document.getElementById("modal-title");
  const formTaskId = document.getElementById("form-task-id");
  const formTitle = document.getElementById("form-task-title");
  const formDesc = document.getElementById("form-task-desc");
  const formPriority = document.getElementById("form-task-priority");
  const formDueDate = document.getElementById("form-task-due-date");
  const formStatusGroup = document.getElementById("form-status-group");
  const formStatus = document.getElementById("form-task-status");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalCancelBtn = document.getElementById("modal-cancel-btn");
  const openNewTaskModalBtn = document.getElementById("open-new-task-modal-btn");
  const quickAddBtn = document.getElementById("btn-quick-add");

  // -----------------------------------------------------------------
  // Initialization
  // -----------------------------------------------------------------
  function init() {
    renderCurrentDate();
    fetchTasksAndStats();
    attachEventListeners();
  }

  function renderCurrentDate() {
    if (!currentDateDisplay) return;
    const now = new Date();
    const options = { weekday: "short", month: "short", day: "numeric", year: "numeric" };
    currentDateDisplay.textContent = `📅 ${now.toLocaleDateString(undefined, options)}`;
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

  // -----------------------------------------------------------------
  // Helper: Escape HTML
  // -----------------------------------------------------------------
  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // -----------------------------------------------------------------
  // Helper: Format Due Date
  // -----------------------------------------------------------------
  function formatDueDate(dateString) {
    if (!dateString) return { text: "No deadline", className: "" };

    const due = new Date(dateString + "T00:00:00");
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const diffTime = due.getTime() - today.getTime();
    const diffDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return { text: `Overdue (${dateString})`, className: "due-overdue", isOverdue: true };
    } else if (diffDays === 0) {
      return { text: "Due Today", className: "due-today", isDueToday: true };
    } else if (diffDays === 1) {
      return { text: "Due Tomorrow", className: "due-today" };
    } else {
      const options = { month: "short", day: "numeric" };
      return { text: `Due ${due.toLocaleDateString(undefined, options)}`, className: "" };
    }
  }

  // -----------------------------------------------------------------
  // Stats Calculation
  // -----------------------------------------------------------------
  function renderStats(allTasks) {
    const total = allTasks.length;
    const completed = allTasks.filter(t => t.status === "Completed").length;
    const pending = total - completed;

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const overdueCount = allTasks.filter(t => {
      if (t.status === "Completed" || !t.due_date) return false;
      const due = new Date(t.due_date + "T00:00:00");
      return due.getTime() <= today.getTime();
    }).length;

    if (statTotal) statTotal.textContent = total;
    if (statPending) statPending.textContent = pending;
    if (statCompleted) statCompleted.textContent = completed;
    if (statOverdue) statOverdue.textContent = overdueCount;
  }

  // -----------------------------------------------------------------
  // API Fetching & Filtering
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

  // -----------------------------------------------------------------
  // Render Task Cards
  // -----------------------------------------------------------------
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
  // Modal Management (Add / Edit)
  // -----------------------------------------------------------------
  function openTaskModal(task = null) {
    taskForm.reset();
    if (task) {
      // Edit Mode
      modalTitle.textContent = "✏️ Edit Task";
      formTaskId.value = task.id;
      formTitle.value = task.title;
      formDesc.value = task.description || "";
      formPriority.value = task.priority;
      formDueDate.value = task.due_date || "";
      formStatus.value = task.status;
      formStatusGroup.style.display = "block";
    } else {
      // Create Mode
      modalTitle.textContent = "➕ Add New Task";
      formTaskId.value = "";
      formPriority.value = "Medium";
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
    const status = formStatusGroup.style.display === "none" ? "Pending" : formStatus.value;

    if (!title) {
      showToast("Title is required", "error");
      return;
    }

    try {
      let response;
      if (taskId) {
        // PUT update
        response = await fetch(`/api/tasks/${taskId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, description, priority, due_date, status })
        });
      } else {
        // POST create
        response = await fetch("/api/tasks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, description, priority, due_date, status: "Pending" })
        });
      }

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to save task");

      showToast(taskId ? "Task updated successfully!" : "Task added successfully!", "success");
      closeTaskModal();
      fetchTasksAndStats();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // -----------------------------------------------------------------
  // Actions: Complete & Delete
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
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  // -----------------------------------------------------------------
  // Event Listeners
  // -----------------------------------------------------------------
  function attachEventListeners() {
    // Open Modal buttons
    if (openNewTaskModalBtn) openNewTaskModalBtn.addEventListener("click", () => openTaskModal(null));
    if (quickAddBtn) quickAddBtn.addEventListener("click", () => openTaskModal(null));
    if (emptyStateAddBtn) emptyStateAddBtn.addEventListener("click", () => openTaskModal(null));

    // Close Modal buttons
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
