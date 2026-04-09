/* ═══════════════════════════════════════════════════════════════════
   DevTrack – kanban.js
   Drag & drop, task creation/edit/delete, subtasks, detail view
   ═══════════════════════════════════════════════════════════════════ */

let draggedTaskId = null;
let editingTaskId = null;   // null = create mode, number = edit mode

// ── Drag & Drop ────────────────────────────────────────────────────
function onDragStart(event, taskId) {
  draggedTaskId = taskId;
  event.dataTransfer.effectAllowed = 'move';
  event.currentTarget.classList.add('dragging');
}

function onDragEnd(event) {
  event.currentTarget.classList.remove('dragging');
  document.querySelectorAll('.kanban-column').forEach(col =>
    col.classList.remove('drag-over')
  );
}

document.querySelectorAll('.kanban-col-body').forEach(col => {
  col.addEventListener('dragover', e => {
    e.preventDefault();
    col.closest('.kanban-column').classList.add('drag-over');
  });
  col.addEventListener('dragleave', e => {
    if (!col.contains(e.relatedTarget)) {
      col.closest('.kanban-column').classList.remove('drag-over');
    }
  });
});

async function onDrop(event, newStatus) {
  event.preventDefault();
  if (!draggedTaskId) return;

  const col = event.currentTarget.closest('.kanban-column');
  col.classList.remove('drag-over');

  const card = document.querySelector(`[data-task-id="${draggedTaskId}"]`);
  if (!card) return;

  const oldCol = card.closest('.kanban-col-body');
  const newCol = document.getElementById(`tasks-${newStatus}`);

  if (oldCol === newCol) return;  // same column, no-op

  // Optimistic UI update
  newCol.appendChild(card);
  updateColCount(oldCol);
  updateColCount(newCol);
  removeEmptyPlaceholder(newCol);
  checkEmptyColumn(oldCol);

  // Persist to API
  try {
    const res = await fetch(`/api/tasks/${draggedTaskId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus }),
    });
    if (!res.ok) throw new Error('API error');
    showToast(`Movido a "${newStatus.replace('_',' ')}"`, 'success');
  } catch {
    showToast('Error al actualizar tarea', 'error');
  }

  draggedTaskId = null;
}

function updateColCount(colBody) {
  const col = colBody.closest('.kanban-column');
  const count = col.querySelectorAll('.task-card').length;
  col.querySelector('.col-count').textContent = count;
}

function checkEmptyColumn(colBody) {
  if (!colBody.querySelector('.task-card')) {
    if (!colBody.querySelector('.col-empty')) {
      const empty = document.createElement('div');
      empty.className = 'col-empty';
      empty.textContent = 'Arrastra tareas aquí';
      colBody.appendChild(empty);
    }
  }
}

function removeEmptyPlaceholder(colBody) {
  colBody.querySelector('.col-empty')?.remove();
}

// ── Open task modal ────────────────────────────────────────────────
function openTaskModal(defaultStatus = 'backlog') {
  editingTaskId = null;
  document.getElementById('modalTaskTitle').textContent = 'Nueva tarea';
  document.getElementById('saveTaskBtn').textContent = 'Crear tarea';
  document.getElementById('taskTitle').value = '';
  document.getElementById('taskDescription').value = '';
  document.getElementById('taskStatus').value = defaultStatus;
  document.getElementById('taskPriority').value = 'medium';
  document.getElementById('taskDueDate').value = '';
  document.getElementById('subtasksSection').style.display = 'none';

  // Reset label checkboxes
  document.querySelectorAll('.label-checkbox').forEach(cb => cb.checked = false);

  // Pre-select project if filter is active
  if (SELECTED_PROJECT) {
    document.getElementById('taskProject').value = SELECTED_PROJECT;
  }

  openModal('modalTask');
  setTimeout(() => document.getElementById('taskTitle').focus(), 100);
}

// ── Open task detail (edit mode) ───────────────────────────────────
async function openTaskDetail(taskId) {
  try {
    const res = await fetch(`/api/tasks/${taskId}`);
    const task = await res.json();
    editingTaskId = taskId;

    document.getElementById('modalTaskTitle').textContent = 'Editar tarea';
    document.getElementById('saveTaskBtn').textContent = 'Guardar cambios';
    document.getElementById('taskTitle').value = task.title;
    document.getElementById('taskDescription').value = task.description || '';
    document.getElementById('taskStatus').value = task.status;
    document.getElementById('taskPriority').value = task.priority;
    document.getElementById('taskProject').value = task.project_id;
    document.getElementById('taskDueDate').value = task.due_date
      ? task.due_date.substring(0, 10) : '';

    // Labels
    const labelIds = task.labels.map(l => l.id);
    document.querySelectorAll('.label-checkbox').forEach(cb => {
      cb.checked = labelIds.includes(parseInt(cb.value));
    });

    // Subtasks section
    document.getElementById('subtasksSection').style.display = 'block';
    renderSubtasks(task.subtasks, taskId);

    openModal('modalTask');
  } catch (e) {
    showToast('Error al cargar la tarea', 'error');
  }
}

// ── Save task (create or update) ───────────────────────────────────
async function saveTask() {
  const title = document.getElementById('taskTitle').value.trim();
  if (!title) {
    showToast('El título es obligatorio', 'error');
    document.getElementById('taskTitle').focus();
    return;
  }

  const labelIds = Array.from(document.querySelectorAll('.label-checkbox:checked'))
    .map(cb => parseInt(cb.value));

  const payload = {
    title,
    description: document.getElementById('taskDescription').value.trim(),
    status: document.getElementById('taskStatus').value,
    priority: document.getElementById('taskPriority').value,
    project_id: parseInt(document.getElementById('taskProject').value),
    due_date: document.getElementById('taskDueDate').value || null,
    label_ids: labelIds,
  };

  const isEdit = editingTaskId !== null;
  const url = isEdit ? `/api/tasks/${editingTaskId}` : '/api/tasks';
  const method = isEdit ? 'PUT' : 'POST';

  try {
    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error('API error');
    const task = await res.json();

    showToast(isEdit ? 'Tarea actualizada' : 'Tarea creada', 'success');
    closeModal('modalTask');

    // Reload to reflect changes in the board
    setTimeout(() => window.location.reload(), 500);
  } catch {
    showToast('Error al guardar la tarea', 'error');
  }
}

// ── Delete task ────────────────────────────────────────────────────
async function deleteTask(taskId, btn) {
  if (!confirm('¿Eliminar esta tarea permanentemente?')) return;

  try {
    const res = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
    if (!res.ok) throw new Error();

    const card = btn.closest('.task-card');
    const colBody = card.closest('.kanban-col-body');
    card.style.transition = 'all .25s ease';
    card.style.opacity = '0';
    card.style.transform = 'scale(.9)';
    setTimeout(() => {
      card.remove();
      updateColCount(colBody);
      checkEmptyColumn(colBody);
    }, 250);
    showToast('Tarea eliminada', 'success');
  } catch {
    showToast('Error al eliminar la tarea', 'error');
  }
}

// ── Subtasks ───────────────────────────────────────────────────────
function renderSubtasks(subtasks, taskId) {
  const list = document.getElementById('subtasksList');
  list.innerHTML = '';
  subtasks.forEach(s => {
    const item = document.createElement('div');
    item.className = 'subtask-item';
    item.dataset.subtaskId = s.id;
    item.innerHTML = `
      <input type="checkbox" ${s.is_done ? 'checked' : ''}
             onchange="toggleSubtask(${s.id}, this.checked, this)"/>
      <span class="subtask-title ${s.is_done ? 'done' : ''}">${escHtml(s.title)}</span>
      <button class="icon-btn-xs danger" onclick="removeSubtask(${s.id}, this)" title="Eliminar">
        <svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/></svg>
      </button>
    `;
    list.appendChild(item);
  });
}

async function addSubtask() {
  const input = document.getElementById('newSubtaskInput');
  const title = input.value.trim();
  if (!title || !editingTaskId) return;

  try {
    const res = await fetch('/api/subtasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, task_id: editingTaskId }),
    });
    if (!res.ok) throw new Error();
    const subtask = await res.json();
    input.value = '';

    // Add to DOM
    const list = document.getElementById('subtasksList');
    const item = document.createElement('div');
    item.className = 'subtask-item';
    item.dataset.subtaskId = subtask.id;
    item.innerHTML = `
      <input type="checkbox" onchange="toggleSubtask(${subtask.id}, this.checked, this)"/>
      <span class="subtask-title">${escHtml(subtask.title)}</span>
      <button class="icon-btn-xs danger" onclick="removeSubtask(${subtask.id}, this)" title="Eliminar">
        <svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/></svg>
      </button>
    `;
    list.appendChild(item);
  } catch {
    showToast('Error al agregar subtarea', 'error');
  }
}

async function toggleSubtask(id, isDone, checkbox) {
  const label = checkbox.nextElementSibling;
  label.classList.toggle('done', isDone);
  await fetch(`/api/subtasks/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_done: isDone }),
  });
}

async function removeSubtask(id, btn) {
  const item = btn.closest('.subtask-item');
  await fetch(`/api/subtasks/${id}`, { method: 'DELETE' });
  item.style.opacity = '0';
  setTimeout(() => item.remove(), 200);
}

// ── Keyboard shortcut: N = new task ────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'n' && !e.ctrlKey && !e.metaKey &&
      document.activeElement.tagName !== 'INPUT' &&
      document.activeElement.tagName !== 'TEXTAREA') {
    openTaskModal();
  }
});

// ── Utility ────────────────────────────────────────────────────────
function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Add Enter key support for subtask input
document.getElementById('newSubtaskInput')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') { e.preventDefault(); addSubtask(); }
});
