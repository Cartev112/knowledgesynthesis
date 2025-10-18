// Review Queue JavaScript
let allRelationships = [];
let filteredRelationships = [];
let currentEditId = null;

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

// Fetch relationships
async function fetchRelationships() {
  const loading = document.getElementById('loading');
  const list = document.getElementById('relationships-list');
  
  loading.classList.remove('hidden');
  list.innerHTML = '';
  
  try {
    const statusFilter = document.getElementById('filter-status').value;
    console.log('Fetching review queue with status:', statusFilter);
    const response = await fetch(`/review/queue?limit=100&status_filter=${statusFilter}`);
    
    console.log('Review queue response status:', response.status);
    if (!response.ok) throw new Error('Failed to fetch relationships');
    
    const data = await response.json();
    console.log('Review queue data:', data);
    // Backend returns 'items' not 'relationships'
    allRelationships = data.items || data.relationships || [];
    console.log('Relationships count:', allRelationships.length);
    
    loading.classList.add('hidden');
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
    noResults.classList.remove('hidden');
    noResults.style.display = 'block';
    return;
  }
  
  noResults.classList.add('hidden');
  
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
        ${rel.status === 'unverified' ? `
          <button class="action-btn btn-verify" onclick="verifyRelationship('${rel.relationship_id}')">
            ✓ Verify
          </button>
          <button class="action-btn btn-incorrect" onclick="flagRelationship('${rel.relationship_id}')">
            ✗ Incorrect
          </button>
        ` : ''}
        <button class="action-btn btn-edit" onclick="openEditModal('${rel.relationship_id}')">
          ✏️ Edit
        </button>
      </div>
    </div>
  `).join('');
}

// Verify relationship
async function verifyRelationship(relationshipId) {
  try {
    const response = await fetch(`/review/${relationshipId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reviewer_id: 'expert-user',
        reviewer_first_name: '',
        reviewer_last_name: ''
      })
    });
    
    if (!response.ok) throw new Error('Failed to verify');
    
    alert('✓ Relationship verified!');
    fetchStats();
    fetchRelationships();
    
  } catch (error) {
    console.error('Error verifying:', error);
    alert('Error verifying relationship');
  }
}

// Flag relationship
async function flagRelationship(relationshipId) {
  const reason = prompt('Why is this relationship incorrect?');
  if (!reason) return;
  
  try {
    const response = await fetch(`/review/${relationshipId}/flag`, {
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
    
    alert('✓ Relationship flagged as incorrect!');
    fetchStats();
    fetchRelationships();
    
  } catch (error) {
    console.error('Error flagging:', error);
    alert('Error flagging relationship');
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
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    if (!response.ok) throw new Error('Failed to save');
    
    alert('✓ Changes saved!');
    closeEditModal();
    fetchRelationships();
    
  } catch (error) {
    console.error('Error saving:', error);
    alert('Error saving changes');
  }
}

// Auto-refresh stats every 30 seconds
setInterval(() => {
  fetchStats();
}, 30000);
