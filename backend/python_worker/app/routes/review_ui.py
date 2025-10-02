"""Review UI for expert curation of knowledge graph extractions."""
from fastapi import APIRouter, Response


router = APIRouter()


HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Knowledge Graph Review Queue</title>
    <style>
      * { box-sizing: border-box; }
      html, body { height: 100%; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
      body { background: #f9fafb; }
      
      #header {
        background: white;
        border-bottom: 1px solid #e5e7eb;
        padding: 16px 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      }
      
      h1 { margin: 0; font-size: 24px; font-weight: 600; color: #111827; }
      
      #stats {
        display: flex;
        gap: 24px;
        margin-top: 12px;
      }
      
      .stat {
        display: flex;
        flex-direction: column;
        padding: 8px 16px;
        background: #f3f4f6;
        border-radius: 6px;
      }
      
      .stat-label { font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }
      .stat-value { font-size: 20px; font-weight: 600; margin-top: 4px; }
      .stat-unverified .stat-value { color: #dc2626; }
      .stat-verified .stat-value { color: #059669; }
      .stat-incorrect .stat-value { color: #d97706; }
      
      #controls {
        padding: 16px 24px;
        background: white;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        gap: 12px;
        align-items: center;
      }
      
      select, button {
        padding: 8px 16px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 14px;
        background: white;
        cursor: pointer;
      }
      
      button {
        background: #3b82f6;
        color: white;
        border: none;
        font-weight: 500;
      }
      
      button:hover { background: #2563eb; }
      button:disabled { background: #9ca3af; cursor: not-allowed; }
      
      #queue {
        padding: 24px;
        max-width: 1200px;
        margin: 0 auto;
      }
      
      .review-item {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
      }
      
      .triplet {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
        font-size: 16px;
      }
      
      .entity {
        padding: 8px 16px;
        background: #dbeafe;
        color: #1e40af;
        border-radius: 6px;
        font-weight: 500;
      }
      
      .predicate {
        padding: 8px 16px;
        background: #fef3c7;
        color: #92400e;
        border-radius: 6px;
        font-style: italic;
      }
      
      .metadata {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin-bottom: 16px;
        font-size: 13px;
        color: #6b7280;
      }
      
      .meta-item {
        display: flex;
        flex-direction: column;
      }
      
      .meta-label { font-weight: 600; color: #374151; margin-bottom: 4px; }
      
      .original-text {
        background: #f3f4f6;
        padding: 12px;
        border-radius: 6px;
        border-left: 3px solid #3b82f6;
        margin-bottom: 16px;
        font-size: 14px;
        line-height: 1.6;
        color: #1f2937;
      }
      
      .actions {
        display: flex;
        gap: 8px;
      }
      
      .btn-confirm {
        background: #059669;
        color: white;
        padding: 8px 20px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
      }
      
      .btn-confirm:hover { background: #047857; }
      
      .btn-flag {
        background: #dc2626;
        color: white;
        padding: 8px 20px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
      }
      
      .btn-flag:hover { background: #b91c1c; }
      
      .btn-edit {
        background: #f59e0b;
        color: white;
        padding: 8px 20px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
      }
      
      .btn-edit:hover { background: #d97706; }
      
      .status-indicator {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
      }
      
      .status-unverified { background: #fee2e2; color: #991b1b; }
      .status-verified { background: #d1fae5; color: #065f46; }
      .status-incorrect { background: #fed7aa; color: #92400e; }
      
      #message {
        position: fixed;
        top: 80px;
        right: 24px;
        padding: 12px 20px;
        border-radius: 6px;
        background: #10b981;
        color: white;
        font-weight: 500;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        display: none;
        z-index: 1000;
      }
      
      #message.show { display: block; animation: slideIn 0.3s; }
      
      @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
    </style>
  </head>
  <body>
    <div id="header">
      <h1>Knowledge Graph Review Queue</h1>
      <div id="stats">
        <div class="stat stat-unverified">
          <div class="stat-label">Unverified</div>
          <div class="stat-value" id="stat-unverified">-</div>
        </div>
        <div class="stat stat-verified">
          <div class="stat-label">Verified</div>
          <div class="stat-value" id="stat-verified">-</div>
        </div>
        <div class="stat stat-incorrect">
          <div class="stat-label">Flagged</div>
          <div class="stat-value" id="stat-incorrect">-</div>
        </div>
      </div>
    </div>
    
    <div id="controls">
      <label>
        Filter:
        <select id="status-filter">
          <option value="unverified">Unverified Only</option>
          <option value="verified">Verified Only</option>
          <option value="incorrect">Flagged Only</option>
        </select>
      </label>
      <button id="refresh-btn">Refresh Queue</button>
    </div>
    
    <div id="queue">
      <p style="text-align: center; color: #6b7280;">Loading...</p>
    </div>
    
    <div id="message"></div>
    
    <script>
      const queueEl = document.getElementById('queue');
      const statusFilter = document.getElementById('status-filter');
      const refreshBtn = document.getElementById('refresh-btn');
      const messageEl = document.getElementById('message');
      
      async function fetchStats() {
        const res = await fetch('/review/stats');
        const data = await res.json();
        document.getElementById('stat-unverified').textContent = data.unverified;
        document.getElementById('stat-verified').textContent = data.verified;
        document.getElementById('stat-incorrect').textContent = data.incorrect;
      }
      
      async function fetchQueue() {
        const status = statusFilter.value;
        const res = await fetch(`/review/queue?status_filter=${status}&limit=50`);
        const data = await res.json();
        
        if (!data.items || data.items.length === 0) {
          queueEl.innerHTML = '<p style="text-align: center; color: #6b7280;">No items in queue</p>';
          return;
        }
        
        queueEl.innerHTML = data.items.map(item => `
          <div class="review-item" data-rel-id="${item.relationship_id}">
            <div class="triplet">
              <span class="entity">${escapeHtml(item.subject)}</span>
              <span class="predicate">${escapeHtml(item.predicate)}</span>
              <span class="entity">${escapeHtml(item.object)}</span>
              <span class="status-indicator status-${item.status}">${item.status}</span>
            </div>
            
            ${item.original_text ? `
              <div class="original-text">
                "${escapeHtml(item.original_text)}"
              </div>
            ` : ''}
            
            <div class="metadata">
              <div class="meta-item">
                <div class="meta-label">Subject Type</div>
                <div>${item.subject_type || 'N/A'}</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">Object Type</div>
                <div>${item.object_type || 'N/A'}</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">Confidence</div>
                <div>${item.confidence !== null ? (item.confidence * 100).toFixed(0) + '%' : 'N/A'}</div>
              </div>
              <div class="meta-item">
                <div class="meta-label">Sources</div>
                <div>${item.documents.length} document(s)</div>
              </div>
            </div>
            
            <div class="actions">
              <button class="btn-confirm" onclick="confirmRelationship('${item.relationship_id}')">
                ✓ Confirm
              </button>
              <button class="btn-edit" onclick="editRelationship('${item.relationship_id}')">
                ✎ Edit
              </button>
              <button class="btn-flag" onclick="flagRelationship('${item.relationship_id}')">
                ⚠ Flag as Incorrect
              </button>
            </div>
          </div>
        `).join('');
      }
      
      // Get current user info
      let currentUser = null;
      
      async function getCurrentUser() {
        try {
          const res = await fetch('/api/auth/me', { credentials: 'include' });
          if (res.ok) {
            const data = await res.json();
            currentUser = data.user;
          }
        } catch (e) {
          console.warn('Could not get current user:', e);
        }
      }
      
      async function confirmRelationship(relId) {
        try {
          const payload = { 
            reviewer_id: currentUser?.email || currentUser?.user_id || 'expert-user',
            reviewer_first_name: currentUser?.first_name || '',
            reviewer_last_name: currentUser?.last_name || ''
          };
          
          const res = await fetch(`/review/${relId}/confirm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          
          if (!res.ok) throw new Error('Failed to confirm');
          
          showMessage('Relationship confirmed!', 'success');
          await fetchQueue();
          await fetchStats();
        } catch (e) {
          showMessage('Error: ' + e.message, 'error');
        }
      }
      
      async function flagRelationship(relId) {
        const reason = prompt('Why is this relationship incorrect?');
        if (!reason) return;
        
        try {
          const payload = {
            reason,
            reviewer_id: currentUser?.email || currentUser?.user_id || 'expert-user',
            reviewer_first_name: currentUser?.first_name || '',
            reviewer_last_name: currentUser?.last_name || ''
          };
          
          const res = await fetch(`/review/${relId}/flag`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          
          if (!res.ok) throw new Error('Failed to flag');
          
          showMessage('Relationship flagged!', 'warning');
          await fetchQueue();
          await fetchStats();
        } catch (e) {
          showMessage('Error: ' + e.message, 'error');
        }
      }
      
      async function editRelationship(relId) {
        const confidence = prompt('Enter new confidence score (0-1):');
        if (!confidence) return;
        
        try {
          const payload = {
            confidence: parseFloat(confidence),
            reviewer_id: currentUser?.email || currentUser?.user_id || 'expert-user',
            reviewer_first_name: currentUser?.first_name || '',
            reviewer_last_name: currentUser?.last_name || ''
          };
          
          const res = await fetch(`/review/${relId}/edit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
          
          if (!res.ok) throw new Error('Failed to edit');
          
          showMessage('Relationship updated!', 'success');
          await fetchQueue();
          await fetchStats();
        } catch (e) {
          showMessage('Error: ' + e.message, 'error');
        }
      }
      
      function showMessage(msg, type) {
        messageEl.textContent = msg;
        messageEl.className = 'show';
        messageEl.style.background = type === 'error' ? '#dc2626' : type === 'warning' ? '#f59e0b' : '#10b981';
        setTimeout(() => messageEl.classList.remove('show'), 3000);
      }
      
      function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
      }
      
      statusFilter.addEventListener('change', fetchQueue);
      refreshBtn.addEventListener('click', () => {
        fetchQueue();
        fetchStats();
      });
      
      // Initial load
      getCurrentUser();
      fetchQueue();
      fetchStats();
      
      // Auto-refresh every 30 seconds
      setInterval(() => {
        fetchStats();
      }, 30000);
    </script>
  </body>
</html>
""".strip()


@router.get("")
def serve_review_ui():
    """Serve the review/curation interface."""
    return Response(content=HTML, media_type="text/html")

