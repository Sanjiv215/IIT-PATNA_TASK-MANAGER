/**
 * Student Task Manager - Frontend JavaScript
 * Handles REST API interactions, dynamic DOM updates, filtering, searching, and modals.
 */

document.addEventListener("DOMContentLoaded", () => {
  // State management
  let tasks = [];
  let activeStatusFilter = "";
  let activePriorityFilter = "";
  let searchQuery = "";
  let searchDebounceTimeout = null;

  // DOM Elements
  const tasksContainer = document.getElementById("tasks-container");
  const emptyState = document.getElementById("empty-state");
  const visibleCountBadge = document.getElementById("visible-count");
  const currentDateDisplay = document.getElementById("current-date-display");

  // Stats DOM
  const statTotal = document.getElementById("stat-total");
  const statPending = document.getElementById("stat-pending");
  const statCompleted = document.getElementById("stat-completed");
  const statHigh = document.getElementById("stat-high");

  // Add Task Form
  const addTaskForm = document.getElementById("add-task-form");
  const searchInput = document.getElementById("search-input");
  const clearSearchBtn = document.getElementById("clear-search-btn");
  const resetFiltersBtn = document.getElementById("reset-filters-btn");
  const statusFilterButtons = document.querySelectorAll("#status-filters .segment-btn");
  const priorityFilterButtons = document.querySelectorAll("#priority-filters .segment-btn");

  // Edit Modal DOM
  const editModal = document.getElementById("edit-modal");
  const editTaskForm = document.getElementById("edit-task-form");
  const editTaskId = document.getElementById("edit-task-id");
  const editTaskTitle = document.getElementById("edit-task-title");
  const editTaskDesc = document.getElementById("edit-task-desc");
  const editTaskPriority = document.getElementById("edit-task-priority");
  const editTaskDueDate = document.getElementById("edit-task-due-date");
  const editTaskStatus = document.getElementById("edit-task-status");
  const closeModalBtn = document.getElementById("close-modal-btn");
  const cancelModalBtn = document.getElementById("cancel-modal-btn");

  // -----------------------------------------------------------------
  // Initial Setup
  // -----------------------------------------------------------------
  function init() {
    renderCurrentDate();
    fetchTasks();
    attachEventListeners();
  }

  function renderCurrentDate() {
    const now = new Date();
    const options = { weekday: "short", month: "short", day: "numeric", year: "numeric" };
    currentDateDisplay.textContent = `📅 ${now.toLocaleDateString(undefined, options)}`;
  }

  // -----------------------------------------------------------------
  // Toast Notifications
  // -----------------------------------------------------------------
  function showToast(message, type = "success") {
    const container = document.getElementById("toast-container");
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
  // Helper: Escape HTML to avoid XSS
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
    if (!dateString) return { text: "No due date", className: "" };

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
      return { text: `Due: ${due.toLocaleDateString(undefined, options)}`, className: "" };
    }
  }

  // -----------------------------------------------------------------
  // API Calls
  // -----------------------------------------------------------------
  async function fetchTasks() {
    try {
      let url = "/api/tasks";
      const params = new URLSearchParams();

      if (searchQuery.trim()) {
        url = "/api/tasks/search";
        params.append("q", searchQuery.trim());
      } else {
        if (activeStatusFilter) params.append("status", activeStatusFilter);
        if (activePriorityFilter) params.append("priority", activePriorityFilter);
      }

      const queryString = params.toString();
      const finalUrl = queryString ? `${url}?${queryString}` : url;

      const response = await fetch(finalUrl);
      if (!response.ok) throw new Error("Failed to load tasks");
      tasks = await response.json();

      // If we used search endpoint, client-side apply any active status/priority filter
      let displayedTasks = tasks;
      if (searchQuery.trim()) {
        if (activeStatusFilter) {
          displayedTasks = displayedTasks.filter(t => t.status === activeStatusFilter);
        }
        if (activePriorityFilter) {
          displayedTasks = displayedTasks.filter(t => t.priority === activePriorityFilter);
        }
      }

      renderTasks(displayedTasks);
      updateOverallStats();
    } catch (err) {
      console.error(err);
      showToast("Could not load tasks from server", "error");
    }
  }

  async function updateOverallStats() {
    try {
      // Fetch all unfiltered tasks to keep stats accurate
      const res = await fetch("/api/tasks");
      if (!res.ok) return;
      const allTasks = await res.json();

      const total = allTasks.length;
      const completed = allTasks.filter(t => t.status === "Completed").length;
      const pending = total - completed;
      const high = allTasks.filter(t => t.priority === "High" && t.status === "Pending").length;

      statTotal.textContent = total;
      statPending.textContent = pending;
      statCompleted.textContent = completed;
      statHigh.textContent = high;
    } catch (e) {
      console.error("Error updating stats", e);
    }
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
          <div class="task-title-group">
            <input type="checkbox" class="task-checkbox" ${isCompleted ? "checked" : ""} title="Mark complete/pending">
            <h3 class="task-title">${escapeHtml(task.title)}</h3>
          </div>
          <div class="task-badges">
            <span class="badge ${priorityClass}">${escapeHtml(task.priority)}</span>
            <span class="badge ${statusClass}">${escapeHtml(task.status)}</span>
          </div>
        </div>

        ${task.description ? `<p class="task-desc">${escapeHtml(task.description)}</p>` : ""}

        <div class="task-card-footer">
          <div class="task-due-info ${dueInfo.className}">
            <span>🗓️</span> <span>${escapeHtml(dueInfo.text)}</span>
          </div>
          <div class="task-actions">
            <button class="btn btn-secondary btn-sm edit-task-btn" title="Edit task">✏️ Edit</button>
            <button class="btn btn-danger btn-sm delete-task-btn" title="Delete task">🗑️ Delete</button>
          </div>
        </div>
      `;

      // Event: Checkbox complete toggle
      const checkbox = card.querySelector(".task-checkbox");
      checkbox.addEventListener("change", () => toggleComplete(task.id, checkbox.checked));

      // Event: Edit button
      const editBtn = card.querySelector(".edit-task-btn");
      editBtn.addEventListener("click", () => openEditModal(task));

      // Event: Delete button
      const deleteBtn = card.querySelector(".delete-task-btn");
      deleteBtn.addEventListener("click", () => deleteTask(task.id, task.title));

      tasksContainer.appendChild(card);
    });
  }

  // -----------------------------------------------------------------
  // Actions: Add, Toggle Complete, Edit, Delete
  // -----------------------------------------------------------------
  addTaskForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const title = document.getElementById("task-title").value.trim();
    const description = document.getElementById("task-desc").value.trim();
    const priority = document.getElementById("task-priority").value;
    const due_date = document.getElementById("task-due-date").value || null;

    if (!title) {
      showToast("Please enter a task title", "error");
      return;
    }

    try {
      const response = await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, priority, due_date, status: "Pending" })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to create task");

      showToast("Task added successfully!", "success");
      addTaskForm.reset();
      fetchTasks();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

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
      fetchTasks();
    } catch (err) {
      showToast(err.message, "error");
      fetchTasks(); // revert checkbox UI
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
      fetchTasks();
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function openEditModal(task) {
    editTaskId.value = task.id;
    editTaskTitle.value = task.title;
    editTaskDesc.value = task.description || "";
    editTaskPriority.value = task.priority;
    editTaskDueDate.value = task.due_date || "";
    editTaskStatus.value = task.status;
    editModal.style.display = "flex";
  }

  function closeEditModal() {
    editModal.style.display = "none";
  }

  editTaskForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const taskId = editTaskId.value;
    const title = editTaskTitle.value.trim();
    const description = editTaskDesc.value.trim();
    const priority = editTaskPriority.value;
    const due_date = editTaskDueDate.value || null;
    const status = editTaskStatus.value;

    if (!title) {
      showToast("Title is required", "error");
      return;
    }

    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, priority, due_date, status })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Failed to update task");

      showToast("Task updated successfully!", "success");
      closeEditModal();
      fetchTasks();
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // -----------------------------------------------------------------
  // Filter & Search Event Listeners
  // -----------------------------------------------------------------
  function attachEventListeners() {
    // Search input with debounce
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value;
      clearSearchBtn.style.display = searchQuery ? "inline-block" : "none";

      clearTimeout(searchDebounceTimeout);
      searchDebounceTimeout = setTimeout(() => {
        fetchTasks();
      }, 250);
    });

    clearSearchBtn.addEventListener("click", () => {
      searchInput.value = "";
      searchQuery = "";
      clearSearchBtn.style.display = "none";
      fetchTasks();
    });

    // Status Segmented Controls
    statusFilterButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        statusFilterButtons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        activeStatusFilter = btn.getAttribute("data-status");
        fetchTasks();
      });
    });

    // Priority Segmented Controls
    priorityFilterButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        priorityFilterButtons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        activePriorityFilter = btn.getAttribute("data-priority");
        fetchTasks();
      });
    });

    // Reset Filters Button
    resetFiltersBtn.addEventListener("click", () => {
      searchQuery = "";
      searchInput.value = "";
      clearSearchBtn.style.display = "none";

      activeStatusFilter = "";
      statusFilterButtons.forEach(b => b.classList.toggle("active", b.getAttribute("data-status") === ""));

      activePriorityFilter = "";
      priorityFilterButtons.forEach(b => b.classList.toggle("active", b.getAttribute("data-priority") === ""));

      fetchTasks();
    });

    // Modal close controls
    closeModalBtn.addEventListener("click", closeEditModal);
    cancelModalBtn.addEventListener("click", closeEditModal);
    editModal.addEventListener("click", (e) => {
      if (e.target === editModal) closeEditModal();
    });
  }

  // Run initialization
  init();
});
