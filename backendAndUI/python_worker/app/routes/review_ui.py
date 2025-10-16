"""Review UI for expert curation of knowledge graph extractions."""
"""
Knowledge Graph Review Queue UI
================================

This file contains the review/curation interface for the Knowledge Synthesis Platform.
Domain experts use this to verify, edit, or flag AI-extracted relationships.

Structure:
- Python Route Handler (lines 1-10)
- HTML Template (lines 11+)
  - CSS Styles (lines 20-350)
  - HTML Structure (lines 351-460)
  - JavaScript Logic (lines 461-820)

TODO: Consider moving to separate HTML/CSS/JS files for better maintainability
"""
from fastapi import APIRouter, Response


router = APIRouter()


HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Knowledge Graph Review Queue</title>
    
    <!-- ========================================
         CSS STYLES
         ======================================== -->
    <style>
      /* === BASE STYLES === */
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
      
      /* === STATISTICS DISPLAY === */
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
      
      /* === FILTER & CONTROL BAR === */
      #controls {
        padding: 16px 24px;
        background: white;
        border-bottom: 1px solid #e5e7eb;
        display: flex;
        gap: 12px;
        align-items: center;
      }
      
      select, button, input[type="text"] {
        padding: 8px 16px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 14px;
        background: white;
        cursor: pointer;
      }
      
      input[type="text"] {
        min-width: 300px;
        cursor: text;
      }
      
      input[type="text"]::placeholder {
        color: #9ca3af;
      }
      
      button {
        background: #3b82f6;
        color: white;
        border: none;
        font-weight: 500;
      }
      
      button:hover { background: #2563eb; }
      button:disabled { background: #9ca3af; cursor: not-allowed; }
      
      /* === REVIEW QUEUE ITEMS === */
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
      
      /* === EDIT MODAL STYLES === */
      #edit-modal {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 2000;
        align-items: center;
        justify-content: center;
      }
      
      #edit-modal.show { display: flex; }
      
      .modal-content {
        background: white;
        border-radius: 12px;
        padding: 24px;
        max-width: 600px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
      }
      
      .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 2px solid #e5e7eb;
      }
      
      .modal-header h2 {
        margin: 0;
        font-size: 20px;
        color: #111827;
      }
      
      .modal-close {
        background: transparent;
        border: none;
        font-size: 24px;
        cursor: pointer;
        color: #6b7280;
        padding: 0;
        width: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      
      .modal-close:hover { color: #111827; }
      
      .form-group {
        margin-bottom: 16px;
      }
      
      .form-label {
        display: block;
        font-weight: 600;
        color: #374151;
        margin-bottom: 6px;
        font-size: 14px;
      }
      
      .form-input, .form-textarea {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        font-size: 14px;
        font-family: inherit;
      }
      
      .form-input:focus, .form-textarea:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
      }
      
      .form-textarea {
        min-height: 80px;
        resize: vertical;
      }
      
      .modal-actions {
        display: flex;
        gap: 12px;
        justify-content: flex-end;
        margin-top: 24px;
        padding-top: 16px;
        border-top: 1px solid #e5e7eb;
      }
      
      .btn-modal {
        padding: 10px 20px;
        border: none;
        border-radius: 6px;
        font-weight: 500;
        cursor: pointer;
        font-size: 14px;
      }
      
      .btn-cancel {
        background: #f3f4f6;
        color: #374151;
      }
      
      .btn-cancel:hover { background: #e5e7eb; }
      
      .btn-save {
        background: #3b82f6;
        color: white;
      }
      
      .btn-save:hover { background: #2563eb; }
      
      /* === FLAG/REJECTION MODAL === */
      #flag-modal {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 2000;
        align-items: center;
        justify-content: center;
      }
      
      #flag-modal.show { display: flex; }
      
      .flag-comment-area {
        min-height: 120px;
        resize: vertical;
      }
      
      .flag-help-text {
        font-size: 13px;
        color: #6b7280;
        margin-top: 6px;
        line-height: 1.5;
      }
    </style>
  </head>
  <body>
    <!-- ========================================
         HTML STRUCTURE
         ======================================== -->
    
    <!-- === HEADER WITH STATS === -->
    <div id="header">
      <h1>Knowledge Graph Review Queue</h1>
      <div id="node-filter-banner" style="display: none; background: #dbeafe; padding: 8px 16px; border-radius: 6px; margin-top: 12px; font-size: 14px; color: #1e40af;">
        <strong>🔍 Filtered View:</strong> <span id="node-filter-text"></span>
        <button onclick="clearNodeFilter()" style="margin-left: 12px; padding: 4px 12px; background: #3b82f6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">
          Clear Filter
        </button>
      </div>
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
    
    <!-- === FILTER & CONTROL BAR === -->
    <div id="controls">
      <label>
        Status:
        <select id="status-filter">
          <option value="unverified">Unverified Only</option>
          <option value="verified">Verified Only</option>
          <option value="incorrect">Flagged Only</option>
        </select>
      </label>
      <label>
        Search:
        <input type="text" id="keyword-filter" placeholder="Filter by keyword (subject, predicate, object)..." />
      </label>
      <button id="refresh-btn">Refresh Queue</button>
      <button id="clear-filter-btn" style="background: #6b7280;">Clear Filters</button>
      <label>
        Export:
        <select id="export-format-review" style="padding: 8px 12px;">
          <option value="json">JSON</option>
          <option value="csv">CSV</option>
        </select>
      </label>
      <button id="export-btn" onclick="exportReviewQueue()" style="background: #059669;">💾 Export</button>
    </div>
    
    <!-- === REVIEW QUEUE === -->
    <div id="queue">
      <p style="text-align: center; color: #6b7280;">Loading...</p>
    </div>
    
    <div id="message"></div>
    
    <!-- === EDIT RELATIONSHIP MODAL === -->
    <div id="edit-modal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Edit Relationship</h2>
          <button class="modal-close" onclick="closeEditModal()">×</button>
        </div>
        
        <form id="edit-form" onsubmit="saveEdit(event)">
          <div class="form-group">
            <label class="form-label">Subject (Entity 1)</label>
            <input type="text" id="edit-subject" class="form-input" required />
          </div>
          
          <div class="form-group">
            <label class="form-label">Predicate (Relationship Type)</label>
            <input type="text" id="edit-predicate" class="form-input" list="predicate-suggestions" required />
            <datalist id="predicate-suggestions">
              <option value="targets">
              <option value="inhibits">
              <option value="activates">
              <option value="regulates">
              <option value="binds_to">
              <option value="causes">
              <option value="treats">
              <option value="associated_with">
              <option value="located_in">
              <option value="part_of">
            </datalist>
          </div>
          
          <div class="form-group">
            <label class="form-label">Object (Entity 2)</label>
            <input type="text" id="edit-object" class="form-input" required />
          </div>
          
          <div class="form-group">
            <label class="form-label">Confidence (0-1)</label>
            <input type="number" id="edit-confidence" class="form-input" min="0" max="1" step="0.01" />
          </div>
          
          <div class="form-group">
            <label class="form-label">Original Text (Evidence)</label>
            <textarea id="edit-original-text" class="form-textarea"></textarea>
          </div>
          
          <input type="hidden" id="edit-relationship-id" />
          
          <div class="modal-actions">
            <button type="button" class="btn-modal btn-cancel" onclick="closeEditModal()">Cancel</button>
            <button type="submit" class="btn-modal btn-save">Save Changes</button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- === FLAG/REJECTION MODAL === -->
    <div id="flag-modal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>⚠ Flag Relationship as Incorrect</h2>
          <button class="modal-close" onclick="closeFlagModal()">×</button>
        </div>
        
        <form id="flag-form" onsubmit="submitFlag(event)">
          <div class="form-group">
            <label class="form-label">Why is this relationship incorrect?</label>
            <textarea id="flag-comment" class="form-textarea flag-comment-area" required placeholder="Please explain why this relationship is incorrect..."></textarea>
            <div class="flag-help-text">
              <strong>Examples of helpful feedback:</strong><br>
              • "The paper actually states the opposite relationship"<br>
              • "This is a misinterpretation of the original text"<br>
              • "The entities are confused - should be X instead of Y"<br>
              • "This relationship is not supported by the cited evidence"<br>
              • "The predicate is incorrect - it should be 'inhibits' not 'activates'"
            </div>
          </div>
          
          <input type="hidden" id="flag-relationship-id" />
          
          <div class="modal-actions">
            <button type="button" class="btn-modal btn-cancel" onclick="closeFlagModal()">Cancel</button>
            <button type="submit" class="btn-modal" style="background: #dc2626; color: white;">Flag as Incorrect</button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- ========================================
         JAVASCRIPT LOGIC
         ======================================== -->
    <script>
      // ==========================================
      // GLOBAL STATE & INITIALIZATION
      // ==========================================
      
      const queueEl = document.getElementById('queue');
      const statusFilter = document.getElementById('status-filter');
      const keywordFilter = document.getElementById('keyword-filter');
      const refreshBtn = document.getElementById('refresh-btn');
      const clearFilterBtn = document.getElementById('clear-filter-btn');
      const messageEl = document.getElementById('message');
      
      let allItems = []; // Store all fetched items for client-side filtering
      let nodeFilter = null; // Store node IDs to filter by
      
      // Check if we have a node filter from URL
      const urlParams = new URLSearchParams(window.location.search);
      const filterNodesParam = urlParams.get('filter_nodes');
      if (filterNodesParam) {
        nodeFilter = filterNodesParam.split(',').map(id => id.trim());
        console.log('Filtering by nodes:', nodeFilter);
        
        // Show filter banner
        const banner = document.getElementById('node-filter-banner');
        const bannerText = document.getElementById('node-filter-text');
        banner.style.display = 'block';
        bannerText.textContent = `Showing relationships for ${nodeFilter.length} selected node${nodeFilter.length > 1 ? 's' : ''}`;
      }
      
      function clearNodeFilter() {
        // Remove filter parameter and reload
        window.location.href = '/review-ui';
      }
      
      // ==========================================
      // DATA FETCHING FUNCTIONS
      // ==========================================
      
      async function fetchStats() {
        const res = await fetch('/review/stats');
        const data = await res.json();
        document.getElementById('stat-unverified').textContent = data.unverified;
        document.getElementById('stat-verified').textContent = data.verified;
        document.getElementById('stat-incorrect').textContent = data.incorrect;
      }
      
      async function fetchQueue() {
        const status = statusFilter.value;
        let url = `/review/queue?status_filter=${status}&limit=50`;
        
        // Add node filter if present
        if (nodeFilter && nodeFilter.length > 0) {
          url += `&node_ids=${encodeURIComponent(nodeFilter.join(','))}`;
        }
        
        const res = await fetch(url);
        const data = await res.json();
        
        if (!data.items || data.items.length === 0) {
          queueEl.innerHTML = '<p style="text-align: center; color: #6b7280;">No items in queue</p>';
          allItems = [];
          return;
        }
        
        allItems = data.items;
        renderQueue(allItems);
      }
      
      function renderQueue(items) {
        if (!items || items.length === 0) {
          queueEl.innerHTML = '<p style="text-align: center; color: #6b7280;">No items match your filters</p>';
          return;
        }
        
        queueEl.innerHTML = items.map(item => `
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
            
            ${item.flag_reason ? `
              <div style="background: #fef3c7; border-left: 3px solid #f59e0b; padding: 12px; border-radius: 6px; margin-top: 12px;">
                <div style="font-weight: 600; color: #92400e; margin-bottom: 6px;">📝 Expert Feedback:</div>
                <div style="color: #78350f; font-size: 14px; line-height: 1.6;">${escapeHtml(item.flag_reason)}</div>
              </div>
            ` : ''}
            
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
      
      // ==========================================
      // RELATIONSHIP REVIEW ACTIONS
      // ==========================================
      
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
      
      function flagRelationship(relId) {
        // Store the relationship ID and show the modal
        document.getElementById('flag-relationship-id').value = relId;
        document.getElementById('flag-modal').classList.add('show');
        document.getElementById('flag-comment').focus();
      }
      
      function closeFlagModal() {
        document.getElementById('flag-modal').classList.remove('show');
        document.getElementById('flag-form').reset();
      }
      
      async function submitFlag(event) {
        event.preventDefault();
        
        const relId = document.getElementById('flag-relationship-id').value;
        const reason = document.getElementById('flag-comment').value.trim();
        
        if (!reason) {
          showMessage('Please provide a reason for flagging this relationship', 'error');
          return;
        }
        
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
          
          closeFlagModal();
          showMessage('Relationship flagged with your feedback!', 'warning');
          await fetchQueue();
          await fetchStats();
        } catch (e) {
          showMessage('Error: ' + e.message, 'error');
        }
      }
      
      function editRelationship(relId) {
        // Find the item in allItems
        const item = allItems.find(i => i.relationship_id === relId);
        if (!item) {
          alert('Relationship not found');
          return;
        }
        
        // Populate the form
        document.getElementById('edit-subject').value = item.subject || '';
        document.getElementById('edit-predicate').value = item.predicate || '';
        document.getElementById('edit-object').value = item.object || '';
        document.getElementById('edit-confidence').value = item.confidence || '';
        document.getElementById('edit-original-text').value = item.original_text || '';
        document.getElementById('edit-relationship-id').value = relId;
        
        // Show the modal
        document.getElementById('edit-modal').classList.add('show');
      }
      
      function closeEditModal() {
        document.getElementById('edit-modal').classList.remove('show');
        document.getElementById('edit-form').reset();
      }
      
      async function saveEdit(event) {
        event.preventDefault();
        
        const relId = document.getElementById('edit-relationship-id').value;
        const subject = document.getElementById('edit-subject').value;
        const predicate = document.getElementById('edit-predicate').value;
        const object = document.getElementById('edit-object').value;
        const confidence = parseFloat(document.getElementById('edit-confidence').value);
        const originalText = document.getElementById('edit-original-text').value;
        
        try {
          const payload = {
            subject: subject,
            predicate: predicate,
            object: object,
            confidence: confidence,
            original_text: originalText,
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
          
          closeEditModal();
          showMessage('Relationship updated successfully!', 'success');
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
      
      // ==========================================
      // FILTERING & EXPORT FUNCTIONS
      // ==========================================
      
      function applyKeywordFilter() {
        const keyword = keywordFilter.value.trim().toLowerCase();
        
        if (!keyword) {
          renderQueue(allItems);
          return;
        }
        
        const filtered = allItems.filter(item => {
          const subject = (item.subject || '').toLowerCase();
          const predicate = (item.predicate || '').toLowerCase();
          const object = (item.object || '').toLowerCase();
          const originalText = (item.original_text || '').toLowerCase();
          
          return subject.includes(keyword) || 
                 predicate.includes(keyword) || 
                 object.includes(keyword) ||
                 originalText.includes(keyword);
        });
        
        renderQueue(filtered);
      }
      
      function clearFilters() {
        keywordFilter.value = '';
        statusFilter.value = 'unverified';
        fetchQueue();
      }
      
      async function exportReviewQueue() {
        if (!allItems || allItems.length === 0) {
          alert('No items to export. Please load the queue first.');
          return;
        }
        
        const format = document.getElementById('export-format-review').value;
        
        try {
          const response = await fetch('/api/export/review', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              format: format,
              items: allItems
            })
          });
          
          if (!response.ok) {
            throw new Error('Export failed');
          }
          
          // Get filename from response headers or use default
          const contentDisposition = response.headers.get('Content-Disposition');
          let filename = `review_queue_${new Date().toISOString().split('T')[0]}.${format}`;
          if (contentDisposition) {
            const matches = /filename="?([^"]+)"?/.exec(contentDisposition);
            if (matches) filename = matches[1];
          }
          
          // Download the file
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          
          showMessage(`Exported ${allItems.length} items as ${format.toUpperCase()}`, 'success');
        } catch (e) {
          showMessage('Export failed: ' + e.message, 'error');
        }
      }
      
      // ==========================================
      // EVENT LISTENERS & APPLICATION STARTUP
      // ==========================================
      
      // Event listeners
      statusFilter.addEventListener('change', fetchQueue);
      keywordFilter.addEventListener('input', applyKeywordFilter);
      refreshBtn.addEventListener('click', () => {
        fetchStats();
        fetchQueue();
      });
      clearFilterBtn.addEventListener('click', clearFilters);
      
      // Initialize
      getCurrentUser().then(() => {
        fetchStats();
        fetchQueue();
      });
      
      // Auto-refresh stats every 30 seconds
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

