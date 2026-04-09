/* ═══════════════════════════════════════════════════════════════════
   DevTrack – main.js
   Global utilities: modal, toast, sidebar, navigation helpers
   ═══════════════════════════════════════════════════════════════════ */

// ── Modal ──────────────────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id).classList.add('open');
  document.getElementById('modalBackdrop').classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
  // Close backdrop only if no other modal is open
  if (!document.querySelector('.modal.open')) {
    document.getElementById('modalBackdrop').classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Close modal on backdrop click
document.getElementById('modalBackdrop')?.addEventListener('click', () => {
  document.querySelectorAll('.modal.open').forEach(m => closeModal(m.id));
});

// Close modal on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal.open').forEach(m => closeModal(m.id));
  }
});

// ── Toast ──────────────────────────────────────────────────────────
function showToast(message, type = 'info', duration = 3000) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icons = {
    success: '✓',
    error: '✕',
    info: 'ℹ',
  };
  toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all .3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Mobile sidebar ─────────────────────────────────────────────────
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const sidebar = document.getElementById('sidebar');

mobileMenuBtn?.addEventListener('click', () => {
  sidebar.classList.toggle('open');
});

// Close sidebar on outside click (mobile)
document.addEventListener('click', (e) => {
  if (sidebar?.classList.contains('open') &&
      !sidebar.contains(e.target) &&
      !mobileMenuBtn?.contains(e.target)) {
    sidebar.classList.remove('open');
  }
});

// ── Project filter (kanban) ────────────────────────────────────────
function filterByProject(projectId) {
  const url = new URL(window.location.href);
  if (projectId) {
    url.searchParams.set('project_id', projectId);
  } else {
    url.searchParams.delete('project_id');
  }
  window.location.href = url.toString();
}
