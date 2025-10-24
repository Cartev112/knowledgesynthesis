// Review Queue JavaScript
let allRelationships = [];
let filteredRelationships = [];
let currentEditId = null;
let currentCommentRelId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  fetchStats();
  fetchRelationships();
  populateTypeFilter();
});

// Fetch statistics
async function fetchStats() {
  try {
    const response = await fetch('/review/stats');
    if (!response.ok) throw new Error('Failed to fetch stats');
    
    const stats = await response.json();
    document.getElementById('stat-unverified').textContent = stats.unverified || 0;
    document.getElementById('stat-verified').textContent = stats.verified || 0;
    document.getElementById('stat-incorrect').textContent = stats.incorrect || 0;
  } catch (error) {
    console.error('Error fetching stats:', error);
  }
}

// Open comment modal
function openCommentModal(relationshipId) {
  currentCommentRelId = relationshipId;
  document.getElementById('comment-text').value = '';
  const modal = document.getElementById('comment-modal');
  if (modal) modal.classList.add('visible');
}

// Close comment modal
function closeCommentModal() {
  const modal = document.getElementById('comment-modal');
  if (modal) modal.classList.remove('visible');
  currentCommentRelId = null;
}

// Submit comment: reuse edge modal endpoint, then auto-verify
async function submitComment() {
  if (!currentCommentRelId) return;
  const text = document.getElementById('comment-text').value.trim();
  if (!text) { showMessage('Please enter a comment', 'error'); return; }
  try {
    const res = await fetch(`/api/relationships/${encodeURIComponent(currentCommentRelId)}/comments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, author: 'expert-user' })
    });
    if (!res.ok) throw new Error('Failed to add comment');
    // Auto-verify
    await fetch(`/review/${encodeURIComponent(currentCommentRelId)}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_id: 'expert-user', reviewer_first_name: '', reviewer_last_name: '' })
    });
    closeCommentModal();
    showMessage('Comment added and relationship verified!', 'success');
    fetchStats();
    fetchRelationships();
  } catch (err) {
    console.error('Comment error:', err);
    showMessage('Error adding comment', 'error');
  }
}

// Fetch relationships
async function fetchRelationships() {
  const loading = document.getElementById('loading');
  const list = document.getElementById('relationships-list');
  
  loading.style.display = 'block';
  list.innerHTML = '';
  
  try {
    const statusFilter = document.getElementById('filter-status').value;
    const workspaceId = sessionStorage.getItem('currentWorkspaceId');
    
    let url = `/review/queue?limit=100&status_filter=${statusFilter}`;
    if (workspaceId) {
      url += `&workspace_id=${workspaceId}`;
      console.log('Fetching review queue for workspace:', workspaceId);
    }
    
    console.log('Fetching review queue with status:', statusFilter);
    const response = await fetch(url);
    
    console.log('Review queue response status:', response.status);
    if (!response.ok) throw new Error('Failed to fetch relationships');
    
    const data = await response.json();
    console.log('Review queue data:', data);
    // Backend returns 'items' not 'relationships'
    allRelationships = data.items || data.relationships || [];
    console.log('Relationships count:', allRelationships.length);
    
    loading.style.display = 'none';
    applyFilters();
    
  } catch (error) {
    console.error('Error fetching relationships:', error);
    loading.textContent = 'Error loading relationships';
  }
}

// Populate type filter
function populateTypeFilter() {
  const typeFilter = document.getElementById('filter-type');
  const types = new Set();
  
  allRelationships.forEach(rel => {
    if (rel.subject_type) types.add(rel.subject_type);
    if (rel.object_type) types.add(rel.object_type);
  });
  
  types.forEach(type => {
    const option = document.createElement('option');
    option.value = type;
    option.textContent = type;
    typeFilter.appendChild(option);
  });
}

// Apply filters
function applyFilters() {
  const typeFilter = document.getElementById('filter-type').value;
  const searchTerm = document.getElementById('search-box').value.toLowerCase();
  
  console.log('Applying filters:', { typeFilter, searchTerm, allRelationshipsCount: allRelationships.length });
  
  filteredRelationships = allRelationships.filter(rel => {
    // Type filter
    if (typeFilter && typeFilter !== 'all' && typeFilter !== '') {
      if (rel.subject_type !== typeFilter && rel.object_type !== typeFilter) {
        return false;
      }
    }
    
    // Search filter
    if (searchTerm) {
      const searchableText = `${rel.subject} ${rel.predicate} ${rel.object} ${rel.original_text || ''}`.toLowerCase();
      if (!searchableText.includes(searchTerm)) {
        return false;
      }
    }
    
    return true;
  });
  
  console.log('Filtered relationships count:', filteredRelationships.length);
  renderRelationships();
}

// Reset filters
function resetFilters() {
  document.getElementById('filter-status').value = 'unverified';
  document.getElementById('filter-type').value = 'all';
  document.getElementById('search-box').value = '';
  fetchRelationships();
}

// Render relationships
function renderRelationships() {
  const list = document.getElementById('relationships-list');
  const noResults = document.getElementById('no-results');
  
  if (filteredRelationships.length === 0) {
    list.innerHTML = '';
    noResults.style.display = 'block';
    return;
  }
  
  noResults.style.display = 'none';
  
  list.innerHTML = filteredRelationships.map(rel => `
    <div class="relationship-card">
      <div class="relationship-header">
        <span class="relationship-status status-${rel.status}">${rel.status}</span>
      </div>
      
      <div class="relationship-content">
        <div>
          <span class="entity">${rel.subject}</span>
          ${rel.subject_type ? `<span style="color: #6b7280; font-size: 12px;"> (${rel.subject_type})</span>` : ''}
        </div>
        <div class="predicate">→ ${rel.predicate} →</div>
        <div>
          <span class="entity">${rel.object}</span>
          ${rel.object_type ? `<span style="color: #6b7280; font-size: 12px;"> (${rel.object_type})</span>` : ''}
        </div>
      </div>
      
      ${rel.original_text ? `
        <div class="evidence">
          "${rel.original_text}"
        </div>
      ` : ''}
      
      <div class="metadata">
        ${rel.confidence ? `<div>Confidence: ${(rel.confidence * 100).toFixed(0)}%</div>` : ''}
        ${rel.created_at ? `<div>Created: ${new Date(rel.created_at).toLocaleDateString()}</div>` : ''}
        ${rel.documents && rel.documents.length > 0 ? `<div>Sources: ${rel.documents.length}</div>` : ''}
      </div>
      
      ${rel.flag_reason ? `
        <div style="background: #fee2e2; padding: 8px; border-radius: 4px; margin-top: 12px; font-size: 13px; color: #991b1b;">
          <strong>Flagged:</strong> ${rel.flag_reason}
        </div>
      ` : ''}
      
      <div class="actions">
        <button class="action-btn btn-edit" onclick="openEditModal('${rel.relationship_id}')">
          ✏️ Edit
        </button>
        <button class="action-btn btn-comment" onclick="openCommentModal('${rel.relationship_id}')">
          💬 Add Comment
        </button>
      </div>
    </div>
  `).join('');
}

// Confirm relationship (matches original review-ui.py)
async function confirmRelationship(relationshipId) {
  try {
    const response = await fetch(`/review/${relationshipId}/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reviewer_id: 'expert-user',
        reviewer_first_name: '',
        reviewer_last_name: ''
      })
    });
    
    if (!response.ok) throw new Error('Failed to confirm');
    
    showMessage('✓ Relationship confirmed!', 'success');
    fetchStats();
    fetchRelationships();
    
  } catch (error) {
    console.error('Error confirming:', error);
    showMessage('Error confirming relationship', 'error');
  }
}

// Flag relationship - open modal
function flagRelationship(relationshipId) {
  currentEditId = relationshipId;
  document.getElementById('flag-modal').classList.add('visible');
  document.getElementById('flag-comment').focus();
}

// Close flag modal
function closeFlagModal() {
  document.getElementById('flag-modal').classList.remove('visible');
  document.getElementById('flag-comment').value = '';
  currentEditId = null;
}

// Submit flag
async function submitFlag(event) {
  event.preventDefault();
  
  const reason = document.getElementById('flag-comment').value.trim();
  if (!reason) {
    showMessage('Please provide a reason for flagging', 'error');
    return;
  }
  
  try {
    const response = await fetch(`/review/${currentEditId}/flag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reason: reason,
        reviewer_id: 'expert-user',
        reviewer_first_name: '',
        reviewer_last_name: ''
      })
    });
    
    if (!response.ok) throw new Error('Failed to flag');
    
    closeFlagModal();
    showMessage('✓ Relationship flagged as incorrect!', 'warning');
    fetchStats();
    fetchRelationships();
    
  } catch (error) {
    console.error('Error flagging:', error);
    showMessage('Error flagging relationship', 'error');
  }
}

// Open edit modal
function openEditModal(relationshipId) {
  const rel = allRelationships.find(r => r.relationship_id === relationshipId);
  if (!rel) return;
  
  currentEditId = relationshipId;
  
  document.getElementById('edit-subject').value = rel.subject || '';
  document.getElementById('edit-predicate').value = rel.predicate || '';
  document.getElementById('edit-object').value = rel.object || '';
  document.getElementById('edit-evidence').value = rel.original_text || '';
  document.getElementById('edit-confidence').value = rel.confidence || 0.9;
  
  document.getElementById('edit-modal').classList.add('visible');
}

// Close edit modal
function closeEditModal() {
  document.getElementById('edit-modal').classList.remove('visible');
  currentEditId = null;
}

// Save edit
async function saveEdit() {
  if (!currentEditId) return;
  
  const data = {
    subject: document.getElementById('edit-subject').value,
    predicate: document.getElementById('edit-predicate').value,
    object: document.getElementById('edit-object').value,
    original_text: document.getElementById('edit-evidence').value,
    confidence: parseFloat(document.getElementById('edit-confidence').value),
    reviewer_id: 'expert-user',
    reviewer_first_name: '',
    reviewer_last_name: ''
  };
  
  try {
    const response = await fetch(`/review/${currentEditId}/edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) throw new Error('Failed to save');
    
    showMessage('✓ Changes saved!', 'success');
    closeEditModal();
    fetchStats();
    fetchRelationships();
    
  } catch (error) {
    console.error('Error saving:', error);
    showMessage('Error saving changes', 'error');
  }
}

// Show message
function showMessage(msg, type) {
  const messageEl = document.getElementById('message');
  if (!messageEl) return;
  
  messageEl.textContent = msg;
  messageEl.className = 'show';
  messageEl.style.background = type === 'error' ? '#dc2626' : type === 'warning' ? '#f59e0b' : '#10b981';
  setTimeout(() => messageEl.classList.remove('show'), 3000);
}

// Export functionality
async function exportReviewQueue() {
  if (!allRelationships || allRelationships.length === 0) {
    showMessage('No items to export', 'error');
    return;
  }
  
  const format = document.getElementById('export-format').value;
  
  try {
    const response = await fetch('/api/export/review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        format: format,
        items: allRelationships
      })
    });
    
    if (!response.ok) throw new Error('Export failed');
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `review_queue_${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    showMessage(`Exported ${allRelationships.length} items as ${format.toUpperCase()}`, 'success');
  } catch (error) {
    console.error('Export error:', error);
    showMessage('Export failed', 'error');
  }
}

// Auto-refresh stats every 30 seconds
setInterval(() => {
  fetchStats();
}, 30000);
