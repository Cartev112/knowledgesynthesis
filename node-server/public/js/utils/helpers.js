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
  messageEl.style.background = type === 'error' ? '#dc2626' : type === 'warning' ? '#f59e0b' : '#10b981';
  messageEl.style.display = 'block';
  setTimeout(() => {
    messageEl.style.display = 'none';
  }, 3000);
}

function createMessageElement() {
  const el = document.createElement('div');
  el.id = 'message';
  el.style.cssText = `
    position: fixed;
    top: 80px;
    right: 24px;
    padding: 12px 20px;
    border-radius: 6px;
    color: white;
    font-weight: 500;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    display: none;
    z-index: 1000;
  `;
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
