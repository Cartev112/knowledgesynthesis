/**
 * Modal Management for Graph Viewer
 * Handles edge, node, and document detail modals
 */
import { state } from '../state.js';

export class ModalManager {
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
    
    content.innerHTML = html;
    modal.classList.add('visible');
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
      
      let html = `
        <div class="modal-section">
          <div class="modal-section-title">Document Information</div>
          <div class="modal-section-content">
            <strong>Title:</strong> ${doc?.title || 'Untitled'}<br>
            <strong>ID:</strong> ${doc?.id || docId}<br>
            ${doc?.created_by ? `<strong>Created by:</strong> ${doc.created_by}<br>` : ''}
            ${doc?.created_at ? `<strong>Created:</strong> ${new Date(doc.created_at).toLocaleString()}<br>` : ''}
          </div>
        </div>
        
        <div class="modal-section">
          <div class="modal-section-title">Extracted Knowledge</div>
          <div class="modal-section-content">
            <strong>Concepts:</strong> ${data.nodes?.length || 0}<br>
            <strong>Relationships:</strong> ${data.relationships?.length || 0}
          </div>
        </div>
      `;
      
      if (data.nodes && data.nodes.length > 0) {
        html += `
          <div class="modal-section">
            <div class="modal-section-title">Concepts Extracted</div>
            <div class="modal-section-content">
              ${data.nodes.slice(0, 20).map(n => `<div style="padding: 4px 0;">🔵 ${n.label || n.id}</div>`).join('')}
              ${data.nodes.length > 20 ? `<div style="margin-top: 8px; color: #6b7280;">... and ${data.nodes.length - 20} more</div>` : ''}
            </div>
          </div>
        `;
      }
      
      if (data.relationships && data.relationships.length > 0) {
        html += `
          <div class="modal-section">
            <div class="modal-section-title">Relationships Extracted</div>
            <div class="modal-section-content">
              ${data.relationships.slice(0, 15).map(r => {
                const source = data.nodes.find(n => n.id === r.source);
                const target = data.nodes.find(n => n.id === r.target);
                return `<div style="padding: 4px 0; font-size: 13px;">
                  ${source?.label || r.source} <span style="color: #8b5cf6; font-weight: 600;">→ ${r.relation}</span> → ${target?.label || r.target}
                </div>`;
              }).join('')}
              ${data.relationships.length > 15 ? `<div style="margin-top: 8px; color: #6b7280;">... and ${data.relationships.length - 15} more</div>` : ''}
            </div>
          </div>
        `;
      }
      
      content.innerHTML = html;
      modal.classList.add('visible');
    } catch (e) {
      console.error('Error loading document details:', e);
      content.innerHTML = `<div class="modal-section"><div class="modal-section-content" style="color: #dc2626;">Failed to load document details</div></div>`;
      modal.classList.add('visible');
    }
  }
}
