/**
 * Utility Helper Functions
 */

export function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

export function showMessage(msg, type = 'success') {
  const messageEl = document.getElementById('message') || createMessageElement();
  messageEl.textContent = msg;
  messageEl.className = 'show';
  // Set background color based on type
  const bgColor = type === 'error' ? '#dc2626' : type === 'warning' ? '#f59e0b' : '#10b981';
  messageEl.style.background = bgColor;
  setTimeout(() => {
    messageEl.classList.remove('show');
  }, 3000);
}

function createMessageElement() {
  const el = document.createElement('div');
  el.id = 'message';
  // Styles are now in custom-classes.css
  document.body.appendChild(el);
  return el;
}

export function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleString();
}

export function debounce(fn, ms) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), ms);
  };
}
