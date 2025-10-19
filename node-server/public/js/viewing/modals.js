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
    
    // Add comments section
    const comments = data.comments || [];
    html += `
      <div class="modal-section">
        <div class="modal-section-title">Comments (${comments.length})</div>
        <div class="modal-section-content">
          <div id="comments-list" class="comments-list">
            ${comments.length === 0 ? '<div class="no-comments">No comments yet. Be the first to add one!</div>' : ''}
            ${comments.map(comment => `
              <div class="comment-item">
                <div class="comment-header">
                  <span class="comment-author">${comment.author || 'Anonymous'}</span>
                  <span class="comment-date">${comment.created_at ? new Date(comment.created_at).toLocaleDateString() : ''}</span>
                </div>
                <div class="comment-text">${comment.text}</div>
              </div>
            `).join('')}
          </div>
          
          <div class="add-comment-section">
            <textarea 
              id="new-comment-text" 
              class="comment-input" 
              placeholder="Add a comment about this relationship..."
              rows="3"
            ></textarea>
            <button 
              class="comment-submit-btn" 
              onclick="window.viewingManager.modalManager.submitComment('${data.id}')"
            >
              💬 Add Comment
            </button>
          </div>
        </div>
      </div>
    `;
    
    content.innerHTML = html;
    modal.classList.add('visible');
  }
  
  async submitComment(relationshipId) {
    const textarea = document.getElementById('new-comment-text');
    const commentText = textarea.value.trim();
    
    if (!commentText) {
      alert('Please enter a comment');
      return;
    }
    
    try {
      const response = await fetch(`/api/relationships/${relationshipId}/comments`, {
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
      
      // Refresh the modal to show new comment
      const edge = state.cy.getElementById(relationshipId);
      if (edge && edge.length > 0) {
        // Refetch edge data with updated comments
        const updatedResponse = await fetch(`/api/relationships/${relationshipId}`);
        if (updatedResponse.ok) {
          const updatedData = await updatedResponse.json();
          this.showEdgeModal(updatedData);
        }
      }
      
      alert('✓ Comment added successfully!');
    } catch (error) {
      console.error('Error adding comment:', error);
      alert('Failed to add comment. Please try again.');
    }
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
      
      <div class="modal-section">
        <div class="modal-section-title">Type</div>
        <div class="modal-section-content">
          ${data.type || 'Entity'}
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
            <strong>Title:</strong> ${doc?.title || 'Untitled'}<br>
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
}
