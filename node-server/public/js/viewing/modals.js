/**
 * Modal Management for Graph Viewer
 * Handles edge, node, and document detail modals
 */
import { state } from '../state.js';

export class ModalManager {
  constructor() {
    this.docModalNodesPage = 1;
    this.docModalRelsPage = 1;
    this.docModalPageSize = 15;
  }
  
  showEdgeModal(data) {
    const modal = document.getElementById('edge-modal-overlay');
    const content = document.getElementById('edge-modal-content');
    
    // Store current relationship ID for comments
    this.currentRelationshipId = data.id;
    this.currentCommentPage = 1;
    this.commentsPerPage = 5;
    this.commentsExpanded = false;
    
    const sourceLabel = state.cy.getElementById(data.source).data().label;
    const targetLabel = state.cy.getElementById(data.target).data().label;
    
    let html = `
      <div class="modal-section">
        <div class="modal-section-title">Relationship</div>
        <div class="modal-section-content">
          <strong>${sourceLabel}</strong>
          <span class="modal-relation">${data.relation || 'relates to'}</span>
          <strong>${targetLabel}</strong>
        </div>
      </div>
      
      <div class="modal-section">
        <div class="modal-section-title">Status & Metadata</div>
        <div class="modal-section-content">
          <span class="modal-badge ${data.status === 'verified' ? 'badge-verified' : 'badge-unverified'}">
            ${data.status === 'verified' ? '✓ Verified' : '⏳ Unverified'}
          </span>
          ${data.polarity === 'negative' ? '<span class="modal-badge badge-negative">⚠ Negative</span>' : ''}
          <div style="margin-top: 12px;">
            <strong>Confidence:</strong> ${data.confidence ? (data.confidence * 100).toFixed(0) + '%' : 'N/A'}<br>
            <strong>Significance:</strong> ${data.significance ? data.significance + '/5' : 'N/A'}
            ${data.page_number ? `<br><strong>Page:</strong> ${data.page_number}` : ''}
          </div>
        </div>
      </div>
    `;
    
    // Add original text if available
    if (data.original_text && data.original_text.trim && data.original_text.trim().length > 0) {
      html += `
        <div class="modal-section">
          <div class="modal-section-title">Original Text</div>
          <div class="modal-section-content">
            <div class="original-text-box">
              "${data.original_text}"
            </div>
          </div>
        </div>
      `;
    }
    
    // Add sources
    if (data.sources && data.sources.length > 0) {
      html += `
        <div class="modal-section">
          <div class="modal-section-title">Sources</div>
          <div class="modal-section-content">
      `;
      data.sources.forEach(source => {
        html += `<div style="margin-bottom: 8px;">
          📄 <strong>${source.title || source.id}</strong>
          ${source.created_by_first_name ? `<br>&nbsp;&nbsp;&nbsp;by ${source.created_by_first_name} ${source.created_by_last_name}` : ''}
        </div>`;
      });
      html += `</div></div>`;
    }
    
    content.innerHTML = `
      <div class="modal-main-content">
        <div>
          ${html}
        </div>
        <button class="toggle-comments-btn" id="toggle-comments-btn" onclick="window.viewingManager.modalManager.toggleComments()">
          💬 Comments
        </button>
      </div>
      <div class="modal-comments-panel" id="modal-comments-panel">
        <div class="comments-panel-header">
          <h3>💬 Comments</h3>
          <button class="close-comments-btn" onclick="window.viewingManager.modalManager.toggleComments()">✕</button>
        </div>
        <div id="comments-content" class="comments-content">
          <div class="loading-comments">Loading comments...</div>
        </div>
      </div>
    `;
    
    modal.classList.add('visible');
    this.loadComments(data.id);
  }
  
  async fetchCommentsCount(relationshipId) {
    try {
      const response = await fetch(`/api/relationships/${relationshipId}/comments`);
      if (response.ok) {
        const comments = await response.json();
        return comments.length;
      }
    } catch (error) {
      console.error('Error fetching comments count:', error);
    }
    return 0;
  }
  
  async loadComments(relationshipId) {
    const commentsContent = document.getElementById('comments-content');
    if (!commentsContent) return;
    
    try {
      const skip = (this.currentCommentPage - 1) * this.commentsPerPage;
      const response = await fetch(`/api/relationships/${relationshipId}/comments?skip=${skip}&limit=${this.commentsPerPage}`);
      
      if (!response.ok) throw new Error('Failed to load comments');
      
      const comments = await response.json();
      const totalComments = comments.length; // TODO: Get total count from API
      const totalPages = Math.ceil(totalComments / this.commentsPerPage);
      
      let html = `
        <div class="comments-list">
          ${comments.length === 0 ? '<div class="no-comments">No comments yet. Be the first to add one!</div>' : ''}
          ${comments.map(comment => `
            <div class="comment-item">
              <div class="comment-header">
                <span class="comment-author">${comment.author || 'Anonymous'}</span>
                <span class="comment-date">${new Date(comment.created_at).toLocaleDateString()}</span>
              </div>
              <div class="comment-text">${comment.text}</div>
            </div>
          `).join('')}
        </div>
        
        ${totalPages > 1 ? `
          <div class="pagination-controls">
            <button 
              class="pagination-btn" 
              onclick="window.viewingManager.modalManager.changeCommentPage(-1)"
              ${this.currentCommentPage === 1 ? 'disabled' : ''}
            >
              ← Previous
            </button>
            <span class="pagination-info">Page ${this.currentCommentPage} of ${totalPages}</span>
            <button 
              class="pagination-btn" 
              onclick="window.viewingManager.modalManager.changeCommentPage(1)"
              ${this.currentCommentPage === totalPages ? 'disabled' : ''}
            >
              Next →
            </button>
          </div>
        ` : ''}
        
        <div class="add-comment-section">
          <textarea 
            id="new-comment-text" 
            class="comment-input" 
            placeholder="Add a comment about this relationship..."
            rows="3"
          ></textarea>
          <button 
            class="comment-submit-btn" 
            onclick="window.viewingManager.modalManager.submitComment()"
          >
            💬 Add Comment
          </button>
        </div>
      `;
      
      commentsContent.innerHTML = html;
      
      // Update toggle button count
      const toggleBtn = document.getElementById('toggle-comments-btn');
      if (toggleBtn) {
        toggleBtn.innerHTML = `💬 Comments (${totalComments})`;
      }
      
    } catch (error) {
      console.error('Error loading comments:', error);
      commentsContent.innerHTML = '<div class="error-message">Failed to load comments</div>';
    }
  }
  
  toggleComments() {
    const modal = document.getElementById('edge-modal');
    const panel = document.getElementById('modal-comments-panel');
    
    if (!modal || !panel) return;
    
    this.commentsExpanded = !this.commentsExpanded;
    
    if (this.commentsExpanded) {
      modal.classList.add('comments-expanded');
      panel.classList.add('visible');
    } else {
      modal.classList.remove('comments-expanded');
      panel.classList.remove('visible');
    }
  }
  
  async submitComment() {
    const textarea = document.getElementById('new-comment-text');
    const commentText = textarea.value.trim();
    
    if (!commentText) {
      alert('Please enter a comment');
      return;
    }
    
    try {
      const response = await fetch(`/api/relationships/${this.currentRelationshipId}/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: commentText,
          author: 'Current User' // TODO: Get from auth
        })
      });
      
      if (!response.ok) throw new Error('Failed to add comment');
      
      // Clear textarea
      textarea.value = '';
      
      // Reload comments
      this.loadComments(this.currentRelationshipId);
      
    } catch (error) {
      console.error('Error adding comment:', error);
      alert('Failed to add comment. Please try again.');
    }
  }
  
  changeCommentPage(direction) {
    this.currentCommentPage += direction;
    this.loadComments(this.currentRelationshipId);
  }
  
  showNodeModal(data) {
    const modal = document.getElementById('node-modal-overlay');
    const content = document.getElementById('node-modal-content');
    
    const sources = data.sources || [];
    let sourcesHtml = '';
    if (sources.length === 0 || !sources || (sources.length === 1 && !sources[0].id)) {
      sourcesHtml = '<div style="color: #ef4444;">No sources recorded</div>';
    } else {
      sourcesHtml = `
        <strong>${sources.length} document(s)</strong>
        <div style="margin-top: 8px;">
          ${sources.map(s => {
            const title = (typeof s === 'object' && s.title) ? s.title : s;
            const firstName = (typeof s === 'object' && s.created_by_first_name) ? s.created_by_first_name : '';
            const lastName = (typeof s === 'object' && s.created_by_last_name) ? s.created_by_last_name : '';
            const userName = firstName && lastName ? ` — by ${firstName} ${lastName}` : '';
            return `<div style="padding: 8px 0; border-bottom: 1px solid #e5e7eb;">📄 ${title}${userName}</div>`;
          }).join('')}
        </div>
      `;
    }
    
    let significanceHtml = '';
    if (data.significance) {
      const stars = '⭐'.repeat(data.significance);
      const emptyStars = '☆'.repeat(5 - data.significance);
      significanceHtml = `
        <div class="modal-section">
          <div class="modal-section-title">Significance</div>
          <div class="modal-section-content" style="font-size: 18px; color: #f59e0b;">
            ${stars}${emptyStars}
            <span style="font-size: 12px; color: #6b7280; margin-left: 8px;">(${data.significance}/5)</span>
          </div>
        </div>
      `;
    }
    
    let html = `
      <div class="modal-section">
        <div class="modal-section-title">Node Label</div>
        <div class="modal-section-content" style="font-weight: 600; font-size: 18px;">
          ${data.label || data.id}
        </div>
      </div>
      
      ${significanceHtml}
      
      <div class="modal-section">
        <div class="modal-section-title">ID</div>
        <div class="modal-section-content" style="font-family: monospace; font-size: 12px;">
          ${data.id}
        </div>
      </div>
      
      <div class="modal-section">
        <div class="modal-section-title">Sources</div>
        <div class="modal-section-content">
          ${sourcesHtml}
        </div>
      </div>
    `;
    
    content.innerHTML = html;
    modal.classList.add('visible');
  }
  
  async showDocumentModal(docId) {
    const modal = document.getElementById('document-modal-overlay');
    const content = document.getElementById('document-modal-content');
    
    try {
      const res = await fetch(`/query/graph_by_docs?doc_ids=${docId}`);
      if (!res.ok) throw new Error('Failed to fetch document data');
      
      const data = await res.json();
      const doc = state.indexData.documents.find(d => d.id === docId);
      
      // Format uploader info
      let uploaderInfo = 'Unknown';
      if (doc?.uploaded_by_first_name || doc?.uploaded_by_last_name) {
        uploaderInfo = `${doc.uploaded_by_first_name || ''} ${doc.uploaded_by_last_name || ''}`.trim();
      } else if (doc?.created_by) {
        uploaderInfo = doc.created_by;
      }
      
      let html = `
        <div class="modal-section">
          <div class="modal-section-title">Document Information</div>
          <div class="modal-section-content">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
              <strong>Title:</strong>
              <input type="text" id="doc-title-input" value="${(doc?.title || 'Untitled').replace(/"/g, '&quot;')}" 
                     style="flex: 1; padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 4px; font-size: 14px;" />
              <button onclick="window.viewingManager.modalManager.saveDocumentTitle('${docId}')" 
                      class="btn-primary" style="padding: 6px 12px; font-size: 13px;">
                💾 Save
              </button>
            </div>
            <strong>ID:</strong> ${doc?.id || docId}<br>
            <strong>Uploaded by:</strong> ${uploaderInfo}<br>
            ${doc?.created_at ? `<strong>Created:</strong> ${new Date(doc.created_at).toLocaleString()}<br>` : ''}
          </div>
        </div>
        
        <div class="modal-section">
          <div class="modal-section-title">Extracted Knowledge Summary</div>
          <div class="modal-section-content">
            <strong>Concepts:</strong> ${data.nodes?.length || 0} &nbsp;&nbsp;&nbsp; <strong>Relationships:</strong> ${data.relationships?.length || 0}
          </div>
        </div>
      `;
      
      // Two-column layout for concepts and relationships
      if ((data.nodes && data.nodes.length > 0) || (data.relationships && data.relationships.length > 0)) {
        html += `<div class="doc-modal-two-column">`;
        
        // Left column: Concepts
        html += `<div class="doc-modal-column">`;
        if (data.nodes && data.nodes.length > 0) {
          const pageSize = this.docModalPageSize;
          const showing = Math.min(this.docModalNodesPage * pageSize, data.nodes.length);
          html += `
            <div class="modal-section">
              <div class="modal-section-title">Concepts (${showing}/${data.nodes.length})</div>
              <div class="modal-section-content doc-modal-list-paginated" id="doc-modal-nodes-list">
                ${data.nodes.slice(0, showing).map(n => `
                  <div class="doc-modal-item" onclick="window.viewingManager.focusNode('${n.id}')">
                    <span class="doc-modal-icon">🔵</span>
                    <span class="doc-modal-text">${n.label || n.id}</span>
                  </div>
                `).join('')}
              </div>
              ${showing < data.nodes.length ? `<button class="doc-modal-show-more" onclick="window.viewingManager.modalManager.showMoreNodes('${docId}', ${data.nodes.length})">Show More (${data.nodes.length - showing} remaining)</button>` : ''}
            </div>
          `;
        }
        html += `</div>`;
        
        // Right column: Relationships
        html += `<div class="doc-modal-column">`;
        if (data.relationships && data.relationships.length > 0) {
          const pageSize = this.docModalPageSize;
          const showing = Math.min(this.docModalRelsPage * pageSize, data.relationships.length);
          html += `
            <div class="modal-section">
              <div class="modal-section-title">Relationships (${showing}/${data.relationships.length})</div>
              <div class="modal-section-content doc-modal-list-paginated" id="doc-modal-rels-list">
                ${data.relationships.slice(0, showing).map(r => {
                  const source = data.nodes.find(n => n.id === r.source);
                  const target = data.nodes.find(n => n.id === r.target);
                  // Use relationship_id or construct edge ID from source-target
                  const edgeId = r.relationship_id || r.id || `${r.source}-${r.target}`;
                  return `
                    <div class="doc-modal-item doc-modal-rel" onclick="window.viewingManager.focusRelationship('${edgeId}')">
                      <div class="doc-modal-rel-text">
                        <span class="doc-modal-rel-node">${source?.label || r.source}</span>
                        <span class="doc-modal-rel-type">${r.relation}</span>
                        <span class="doc-modal-rel-node">${target?.label || r.target}</span>
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
              ${showing < data.relationships.length ? `<button class="doc-modal-show-more" onclick="window.viewingManager.modalManager.showMoreRels('${docId}', ${data.relationships.length})">Show More (${data.relationships.length - showing} remaining)</button>` : ''}
            </div>
          `;
        }
        html += `</div>`;
        html += `</div>`;
      }
      
      content.innerHTML = html;
      modal.classList.add('visible');
    } catch (e) {
      this.docModalNodesPage = 1;
      this.docModalRelsPage = 1;
      console.error('Error loading document details:', e);
      content.innerHTML = `<div class="modal-section"><div class="modal-section-content" style="color: #dc2626;">Failed to load document details</div></div>`;
      modal.classList.add('visible');
    }
  }
  
  async showMoreNodes(docId, totalCount) {
    this.docModalNodesPage++;
    await this.showDocumentModal(docId);
  }
  
  async showMoreRels(docId, totalCount) {
    this.docModalRelsPage++;
    await this.showDocumentModal(docId);
  }
  
  resetDocModalPagination() {
    this.docModalNodesPage = 1;
    this.docModalRelsPage = 1;
  }
  
  async saveDocumentTitle(docId) {
    const input = document.getElementById('doc-title-input');
    if (!input) return;
    
    const newTitle = input.value.trim();
    if (!newTitle) {
      alert('Title cannot be empty');
      return;
    }
    
    try {
      const response = await fetch(`/query/documents/${encodeURIComponent(docId)}/title`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle })
      });
      
      if (!response.ok) {
        throw new Error('Failed to update title');
      }
      
      // Update the local document data
      const doc = state.indexData.documents.find(d => d.id === docId);
      if (doc) {
        doc.title = newTitle;
      }
      
      // Show success message
      const saveBtn = input.nextElementSibling;
      if (saveBtn) {
        const originalText = saveBtn.innerHTML;
        saveBtn.innerHTML = '✓ Saved';
        saveBtn.style.background = '#10b981';
        setTimeout(() => {
          saveBtn.innerHTML = originalText;
          saveBtn.style.background = '';
        }, 2000);
      }
      
      // Refresh the index panel to show updated title
      if (window.viewingManager?.indexManager) {
        window.viewingManager.indexManager.renderIndexItems();
      }
    } catch (error) {
      console.error('Error saving document title:', error);
      alert('Failed to save document title: ' + error.message);
    }
  }
}
