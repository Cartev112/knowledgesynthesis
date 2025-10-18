/**
 * Ingestion Manager - Handles document upload and knowledge extraction
 */
import { API } from '../utils/api.js';
import { state } from '../state.js';
import { showMessage } from '../utils/helpers.js';

export class IngestionManager {
  displayFileName() {
    const fileInput = document.getElementById('pdf-file');
    const fileNameDisplay = document.getElementById('file-name');
    
    if (fileInput.files && fileInput.files.length > 0) {
      if (fileInput.files.length === 1) {
        const fileName = fileInput.files[0].name;
        const fileSize = (fileInput.files[0].size / 1024 / 1024).toFixed(2); // MB
        fileNameDisplay.innerHTML = `<span style="color: #059669; font-weight: 600;">✓</span> ${fileName} <span style="color: #6b7280; font-size: 12px;">(${fileSize} MB)</span>`;
      } else {
        const totalSize = Array.from(fileInput.files).reduce((sum, file) => sum + file.size, 0);
        const totalSizeMB = (totalSize / 1024 / 1024).toFixed(2);
        fileNameDisplay.innerHTML = `<span style="color: #059669; font-weight: 600;">✓</span> ${fileInput.files.length} files selected <span style="color: #6b7280; font-size: 12px;">(${totalSizeMB} MB total)</span>`;
      }
    } else {
      fileNameDisplay.textContent = 'No files selected';
    }
  }
  
  toggleGraphContext() {
    const checkbox = document.getElementById('use-graph-context');
    const statusDiv = document.getElementById('graph-context-status');
    const countSpan = document.getElementById('graph-context-count');
    
    if (checkbox.checked) {
      if (state.selectedNodes.size === 0) {
        alert('Please select nodes in the Viewer first.');
        checkbox.checked = false;
        return;
      }
      countSpan.textContent = state.selectedNodes.size;
      statusDiv.style.display = 'block';
    } else {
      statusDiv.style.display = 'none';
    }
  }
  
  async getGraphContextText() {
    if (state.selectedNodes.size === 0) {
      return null;
    }
    
    try {
      const nodeIds = Array.from(state.selectedNodes);
      const data = await API.getSubgraph(nodeIds);
      
      // Get 1-hop neighbors for richer context
      const neighbors = this._getNeighbors(data.nodes, data.relationships);
      
      let contextText = '=== EXISTING KNOWLEDGE GRAPH CONTEXT ===\n\n';
      contextText += `This subgraph contains ${data.nodes.length} selected entities, ${neighbors.length} neighbor entities, and ${data.relationships.length} relationships:\n\n`;
      
      contextText += 'SELECTED ENTITIES:\n';
      data.nodes.forEach(node => {
        const label = String(node.label || 'Unknown').replace(/[^\w\s-]/g, '');
        const type = String(node.type || 'Concept').replace(/[^\w\s-]/g, '');
        const sig = node.significance ? ` (significance: ${node.significance}/5)` : '';
        contextText += `- ${label} (${type})${sig}\n`;
      });
      
      if (neighbors.length > 0) {
        contextText += '\nNEIGHBOR ENTITIES:\n';
        neighbors.forEach(node => {
          const label = String(node.label || 'Unknown').replace(/[^\w\s-]/g, '');
          const type = String(node.type || 'Concept').replace(/[^\w\s-]/g, '');
          contextText += `- ${label} (${type})\n`;
        });
      }
      
      contextText += '\nRELATIONSHIPS:\n';
      data.relationships.forEach(rel => {
        const sourceNode = data.nodes.find(n => n.id === rel.source) || neighbors.find(n => n.id === rel.source);
        const targetNode = data.nodes.find(n => n.id === rel.target) || neighbors.find(n => n.id === rel.target);
        const sourceName = String(sourceNode ? sourceNode.label : rel.source).replace(/[^\w\s-]/g, '');
        const targetName = String(targetNode ? targetNode.label : rel.target).replace(/[^\w\s-]/g, '');
        const relation = String(rel.relation || 'RELATED_TO').replace(/[^\w\s-]/g, '');
        const conf = rel.confidence ? ` (confidence: ${rel.confidence.toFixed(2)})` : '';
        
        contextText += `- ${sourceName} -> [${relation}] -> ${targetName}${conf}\n`;
      });
      
      contextText += '\n=== END CONTEXT ===\n\n';
      return { text: contextText, data, neighbors };
      
    } catch (error) {
      console.error('Error getting graph context:', error);
      return null;
    }
  }
  
  _getNeighbors(selectedNodes, relationships) {
    // Get unique neighbor node IDs from relationships
    const selectedIds = new Set(selectedNodes.map(n => n.id));
    const neighborIds = new Set();
    
    relationships.forEach(rel => {
      if (selectedIds.has(rel.source) && !selectedIds.has(rel.target)) {
        neighborIds.add(rel.target);
      }
      if (selectedIds.has(rel.target) && !selectedIds.has(rel.source)) {
        neighborIds.add(rel.source);
      }
    });
    
    // Fetch neighbor nodes from cytoscape
    const neighbors = [];
    if (state.cy) {
      neighborIds.forEach(id => {
        const node = state.cy.getElementById(id);
        if (node.length > 0) {
          neighbors.push(node.data());
        }
      });
    }
    
    return neighbors;
  }
  
  async showContextPreview() {
    const modal = document.getElementById('context-preview-modal');
    if (!modal) return;
    
    try {
      const result = await this.getGraphContextText();
      if (!result) {
        alert('Failed to load context');
        return;
      }
      
      const { text, data, neighbors } = result;
      
      // Populate nodes list
      const nodesList = document.getElementById('preview-nodes-list');
      nodesList.innerHTML = data.nodes.map(node => 
        `<div style="padding: 4px 0; color: #374151;">
          🔵 <strong>${node.label || 'Unknown'}</strong> (${node.type || 'Concept'})
          ${node.significance ? `<span style="color: #6b7280; font-size: 12px;"> - Sig: ${node.significance}/5</span>` : ''}
        </div>`
      ).join('');
      
      // Populate relationships list
      const relsList = document.getElementById('preview-relationships-list');
      relsList.innerHTML = data.relationships.map(rel => {
        const source = data.nodes.find(n => n.id === rel.source) || neighbors.find(n => n.id === rel.source);
        const target = data.nodes.find(n => n.id === rel.target) || neighbors.find(n => n.id === rel.target);
        return `<div style="padding: 4px 0; color: #374151; font-size: 13px;">
          ${source?.label || rel.source} <span style="color: #8b5cf6; font-weight: 600;">→ [${rel.relation}] →</span> ${target?.label || rel.target}
          ${rel.confidence ? `<span style="color: #6b7280; font-size: 11px;"> (${(rel.confidence * 100).toFixed(0)}%)</span>` : ''}
        </div>`;
      }).join('');
      
      // Populate neighbors list
      const neighborsList = document.getElementById('preview-neighbors-list');
      if (neighbors.length > 0) {
        neighborsList.innerHTML = neighbors.map(node => 
          `<div style="padding: 4px 0; color: #6b7280; font-size: 13px;">
            ○ ${node.label || 'Unknown'} (${node.type || 'Concept'})
          </div>`
        ).join('');
      } else {
        neighborsList.innerHTML = '<div style="color: #9ca3af; font-style: italic;">No neighbor entities</div>';
      }
      
      // Populate raw text
      document.getElementById('preview-raw-text').textContent = text;
      
      // Estimate tokens (rough: ~4 chars per token)
      const tokenCount = Math.ceil(text.length / 4);
      document.getElementById('preview-token-count').textContent = tokenCount;
      
      // Update counts
      document.getElementById('preview-node-count').textContent = data.nodes.length;
      document.getElementById('preview-rel-count').textContent = data.relationships.length;
      document.getElementById('preview-neighbor-count').textContent = neighbors.length;
      
      // Store text for copying
      this.cachedContextText = text;
      
      // Show modal
      modal.style.display = 'flex';
      
    } catch (error) {
      console.error('Error showing context preview:', error);
      alert('Error loading context preview');
    }
  }
  
  closeContextPreview() {
    const modal = document.getElementById('context-preview-modal');
    if (modal) {
      modal.style.display = 'none';
    }
  }
  
  copyContextText() {
    if (this.cachedContextText) {
      navigator.clipboard.writeText(this.cachedContextText).then(() => {
        alert('✓ Context text copied to clipboard!');
      }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy text');
      });
    }
  }
  
  async ingestDocument() {
    const pdfFiles = document.getElementById('pdf-file').files;
    const text = document.getElementById('text-input').value.trim();
    let extractionContext = document.getElementById('extraction-context').value.trim();
    const maxConcepts = parseInt(document.getElementById('max-concepts').value);
    const maxRelationships = parseInt(document.getElementById('max-relationships').value);
    const model = document.getElementById('model-select').value;
    const useGraphContext = document.getElementById('use-graph-context').checked;
    
    if (pdfFiles.length === 0 && !text) {
      this.showStatus('error', 'Please upload PDF file(s) or paste text');
      return;
    }
    
    // Get graph context if checkbox is checked
    if (useGraphContext) {
      const result = await this.getGraphContextText();
      if (result && result.text) {
        if (extractionContext) {
          extractionContext = result.text + '\nUSER FOCUS: ' + extractionContext;
        } else {
          extractionContext = result.text;
        }
      } else {
        this.showStatus('error', 'Failed to load graph context. Please try again or uncheck the option.');
        return;
      }
    }
    
    const btn = document.getElementById('ingest-btn');
    this.convertButtonToStatusBar('Queuing...');
    btn.disabled = true;
    
    // Handle text input
    if (!pdfFiles.length && text) {
      this.showStatus('processing', 'Queuing text for processing...');
      try {
        const response = await fetch('/api/ingest/text_async', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text,
            document_title: 'Text Upload',
            document_id: `user-${state.currentUser.email || 'anonymous'}-${Date.now()}`,
            user_id: state.currentUser.email || 'anonymous',
            user_first_name: state.currentUser.first_name || '',
            user_last_name: state.currentUser.last_name || '',
            user_email: state.currentUser.email || '',
            max_concepts: maxConcepts,
            max_relationships: maxRelationships,
            extraction_context: extractionContext
            // Note: model parameter removed - backend uses OPENAI_MODEL from env
          })
        });
        
        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to queue job');
        }
        
        const result = await response.json();
        this.showStatus('processing', `✓ Job queued! ID: ${result.job_id}`);
        
        await this.pollJobStatus(result.job_id, 'text');
        
        document.getElementById('text-input').value = '';
        document.getElementById('extraction-context').value = '';
      } catch (e) {
        this.showStatus('error', '✗ Error: ' + e.message);
      } finally {
        this.restoreButton();
        btn.disabled = false;
      }
      return;
    }
    
    // Handle PDF files
    if (pdfFiles.length > 0) {
      this.showProgress(true);
      this.hideStatus();
      
      const files = Array.from(pdfFiles);
      const totalFiles = files.length;
      const results = {
        successful: 0,
        failed: 0,
        totalTriplets: 0,
        jobIds: []
      };
      
      const fileListEl = document.getElementById('progress-modal-files');
      fileListEl.innerHTML = files.map((file, index) => 
        `<div id="file-status-${index}" style="padding: 8px; margin: 4px 0; background: #f9fafb; border-radius: 4px; font-size: 13px; display: flex; align-items: center; gap: 8px;">
          <span>⏳</span>
          <span>${file.name}</span>
        </div>`
      ).join('');
      
      try {
        this.updateProgress(10, 100, 'Queuing files...');
        this.updateStatusBar('Queuing files for processing...');
        
        for (let i = 0; i < files.length; i++) {
          const file = files[i];
          const fileStatusEl = document.getElementById(`file-status-${i}`);
          
          const queueProgress = 10 + ((i / totalFiles) * 20);
          this.updateProgress(queueProgress, 100, `Queuing: ${file.name}`);
          this.updateStatusBar(`Queuing ${i + 1}/${totalFiles}: ${file.name}`);
          
          fileStatusEl.style.background = '#dbeafe';
          fileStatusEl.style.color = '#1e40af';
          fileStatusEl.innerHTML = `<span>📤</span><span>Queuing: ${file.name}</span>`;
          
          try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('user_id', state.currentUser.email || 'anonymous');
            formData.append('user_first_name', state.currentUser.first_name || '');
            formData.append('user_last_name', state.currentUser.last_name || '');
            formData.append('user_email', state.currentUser.email || '');
            formData.append('max_concepts', maxConcepts);
            formData.append('max_relationships', maxRelationships);
            // Note: model parameter removed - backend uses OPENAI_MODEL from env
            if (extractionContext) formData.append('extraction_context', extractionContext);
            
            const response = await fetch('/api/ingest/pdf_async', {
              method: 'POST',
              body: formData
            });
            
            if (!response.ok) {
              const error = await response.json();
              throw new Error(error.detail || 'Failed to queue job');
            }
            
            const result = await response.json();
            results.jobIds.push({
              jobId: result.job_id,
              fileName: file.name,
              index: i
            });
            
            fileStatusEl.innerHTML = `<span>⏳</span><span>Queued: ${file.name}</span>`;
            
          } catch (e) {
            results.failed++;
            fileStatusEl.style.background = '#fee2e2';
            fileStatusEl.style.color = '#991b1b';
            fileStatusEl.innerHTML = `<span>✗</span><span>${file.name} - ${e.message}</span>`;
          }
        }
        
        this.updateProgress(30, 100, 'Processing files...');
        this.updateStatusBar('Processing files in background...');
        
        const pollingPromises = results.jobIds.map(async (jobInfo) => {
          const { jobId, fileName, index } = jobInfo;
          const fileStatusEl = document.getElementById(`file-status-${index}`);
          
          try {
            const jobResult = await this.pollJobStatus(jobId, 'pdf', fileName, index, totalFiles);
            
            if (jobResult.success) {
              results.successful++;
              results.totalTriplets += jobResult.triplets_written || 0;
              
              fileStatusEl.style.background = '#d1fae5';
              fileStatusEl.style.color = '#065f46';
              const written = jobResult.triplets_written || 0;
              fileStatusEl.innerHTML = `<span>✓</span><span>${fileName} (${written} relationships)</span>`;
            } else {
              results.failed++;
              fileStatusEl.style.background = '#fee2e2';
              fileStatusEl.style.color = '#991b1b';
              fileStatusEl.innerHTML = `<span>✗</span><span>${fileName} - ${jobResult.error}</span>`;
            }
          } catch (e) {
            results.failed++;
            fileStatusEl.style.background = '#fee2e2';
            fileStatusEl.style.color = '#991b1b';
            fileStatusEl.innerHTML = `<span>✗</span><span>${fileName} - ${e.message}</span>`;
          }
        });
        
        await Promise.all(pollingPromises);
        
        this.updateProgress(100, 100, 'All files processed!');
        
        // Show summary
        document.getElementById('progress-summary-success').textContent = results.successful;
        document.getElementById('progress-summary-failed').textContent = results.failed;
        document.getElementById('progress-summary-triplets').textContent = results.totalTriplets;
        document.getElementById('progress-modal-summary').style.display = 'block';
        
        // Change button text
        document.getElementById('progress-modal-close-btn').textContent = 'Close';
        
        this.restoreButton();
        if (results.failed === 0) {
          this.showStatus('success', 
            `✓ All ${results.successful} file(s) processed successfully! Total: ${results.totalTriplets} relationships extracted.`
          );
        } else {
          this.showStatus('error', 
            `⚠ Processed ${results.successful} file(s) successfully, ${results.failed} failed. Total: ${results.totalTriplets} relationships extracted.`
          );
        }
        
        document.getElementById('pdf-file').value = '';
        document.getElementById('extraction-context').value = '';
        this.displayFileName();
        
      } catch (e) {
        this.showProgress(false);
        this.showStatus('error', '✗ Error: ' + e.message);
      } finally {
        this.restoreButton();
        btn.disabled = false;
      }
    }
  }
  
  async pollJobStatus(jobId, type, fileName = null, fileIndex = null, totalFiles = null) {
    const maxAttempts = 300;
    let attempts = 0;
    
    return new Promise((resolve, reject) => {
      const pollInterval = setInterval(async () => {
        attempts++;
        
        try {
          const response = await fetch(`/api/ingest/job/${jobId}`);
          
          if (!response.ok) {
            throw new Error('Failed to check job status');
          }
          
          const job = await response.json();
          
          if (type === 'pdf' && fileName && fileIndex !== null && totalFiles) {
            const fileProgressStart = 30 + ((fileIndex / totalFiles) * 60);
            const fileProgressEnd = 30 + (((fileIndex + 1) / totalFiles) * 60);
            
            if (job.status === 'processing') {
              const progress = fileProgressStart + ((fileProgressEnd - fileProgressStart) * 0.5);
              this.updateProgress(progress, 100, `Processing: ${fileName}`);
              this.updateStatusBar(`Processing ${fileIndex + 1}/${totalFiles}: ${fileName}`);
            } else if (job.status === 'completed') {
              this.updateProgress(fileProgressEnd, 100, `Complete: ${fileName}`);
            }
          } else if (type === 'text') {
            if (job.status === 'processing') {
              this.showStatus('processing', `Processing text... (Job: ${jobId})`);
            } else if (job.status === 'completed') {
              this.showStatus('success', `✓ Success! Extracted ${job.triplets_extracted} relationships.`);
            }
          }
          
          if (job.status === 'completed') {
            clearInterval(pollInterval);
            resolve({
              success: true,
              triplets_extracted: job.triplets_extracted,
              triplets_written: job.triplets_written,
              document_title: job.document_title
            });
          } else if (job.status === 'failed') {
            clearInterval(pollInterval);
            resolve({
              success: false,
              error: job.error_message || 'Processing failed'
            });
          } else if (attempts >= maxAttempts) {
            clearInterval(pollInterval);
            resolve({
              success: false,
              error: 'Job timed out after 5 minutes'
            });
          }
          
        } catch (e) {
          if (attempts >= maxAttempts) {
            clearInterval(pollInterval);
            reject(e);
          }
        }
      }, 1000);
    });
  }
  
  convertButtonToStatusBar(statusText) {
    const btn = document.getElementById('ingest-btn');
    btn.classList.add('as-status-bar');
    btn.innerHTML = `
      <span>${statusText}</span>
      <span class="status-icon">⚙️</span>
    `;
    btn.onclick = null;
  }
  
  updateStatusBar(statusText) {
    const btn = document.getElementById('ingest-btn');
    if (btn.classList.contains('as-status-bar')) {
      btn.innerHTML = `
        <span>${statusText}</span>
        <span class="status-icon">⚙️</span>
      `;
    }
  }
  
  restoreButton() {
    const btn = document.getElementById('ingest-btn');
    btn.classList.remove('as-status-bar');
    btn.innerHTML = '🚀 Extract Knowledge';
    btn.onclick = () => this.ingestDocument();
  }
  
  showProgress(show) {
    const modal = document.getElementById('progress-modal');
    if (show) {
      modal.style.display = 'flex';
    } else {
      modal.style.display = 'none';
    }
  }
  
  updateProgress(current, total, statusText) {
    const percentage = Math.round((current / total) * 100);
    document.getElementById('progress-modal-bar').style.width = percentage + '%';
    document.getElementById('progress-modal-percentage').textContent = percentage + '%';
    document.getElementById('progress-modal-count').textContent = `${current} / ${total}`;
    document.getElementById('progress-modal-status').textContent = statusText;
  }
  
  closeProgressModal() {
    this.showProgress(false);
  }
  
  hideStatus() {
    const statusEl = document.getElementById('ingest-status');
    statusEl.className = '';
    statusEl.textContent = '';
  }
  
  showStatus(type, message) {
    const statusEl = document.getElementById('ingest-status');
    statusEl.className = type;
    statusEl.textContent = message;
  }
}
