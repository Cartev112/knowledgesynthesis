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
      
      let contextText = '=== EXISTING KNOWLEDGE GRAPH CONTEXT ===\n\n';
      contextText += `This subgraph contains ${data.nodes.length} entities and ${data.relationships.length} relationships:\n\n`;
      contextText += 'ENTITIES:\n';
      
      data.nodes.forEach(node => {
        const label = String(node.label || 'Unknown').replace(/[^\w\s-]/g, '');
        const type = String(node.type || 'Concept').replace(/[^\w\s-]/g, '');
        contextText += `- ${label} (${type})\n`;
      });
      
      contextText += '\nRELATIONSHIPS:\n';
      
      data.relationships.forEach(rel => {
        const sourceNode = data.nodes.find(n => n.id === rel.source);
        const targetNode = data.nodes.find(n => n.id === rel.target);
        const sourceName = String(sourceNode ? sourceNode.label : rel.source).replace(/[^\w\s-]/g, '');
        const targetName = String(targetNode ? targetNode.label : rel.target).replace(/[^\w\s-]/g, '');
        const relation = String(rel.relation || 'RELATED_TO').replace(/[^\w\s-]/g, '');
        
        contextText += `- ${sourceName} -> [${relation}] -> ${targetName}\n`;
      });
      
      contextText += '\n=== END CONTEXT ===\n\n';
      return contextText;
      
    } catch (error) {
      console.error('Error getting graph context:', error);
      return null;
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
      const graphContext = await this.getGraphContextText();
      if (graphContext) {
        if (extractionContext) {
          extractionContext = graphContext + '\nUSER FOCUS: ' + extractionContext;
        } else {
          extractionContext = graphContext;
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
      
      const fileListEl = document.getElementById('file-list-status');
      fileListEl.innerHTML = files.map((file, index) => 
        `<div id="file-status-${index}" class="file-status-item pending">
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
          
          fileStatusEl.className = 'file-status-item processing';
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
            fileStatusEl.className = 'file-status-item error';
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
              
              fileStatusEl.className = 'file-status-item success';
              const written = jobResult.triplets_written || 0;
              fileStatusEl.innerHTML = `<span>✓</span><span>${fileName} (${written} relationships)</span>`;
            } else {
              results.failed++;
              fileStatusEl.className = 'file-status-item error';
              fileStatusEl.innerHTML = `<span>✗</span><span>${fileName} - ${jobResult.error}</span>`;
            }
          } catch (e) {
            results.failed++;
            fileStatusEl.className = 'file-status-item error';
            fileStatusEl.innerHTML = `<span>✗</span><span>${fileName} - ${e.message}</span>`;
          }
        });
        
        await Promise.all(pollingPromises);
        
        this.updateProgress(100, 100, 'All files processed!');
        this.updateStatusBar('✓ Complete!');
        setTimeout(() => {
          this.showProgress(false);
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
        }, 1500);
        
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
    const progressContainer = document.getElementById('progress-container');
    if (show) {
      progressContainer.classList.add('active');
    } else {
      progressContainer.classList.remove('active');
    }
  }
  
  updateProgress(current, total, statusText) {
    const percentage = Math.round((current / total) * 100);
    document.getElementById('progress-bar-fill').style.width = percentage + '%';
    document.getElementById('progress-percentage').textContent = percentage + '%';
    document.getElementById('progress-count').textContent = `${current} / ${total}`;
    document.getElementById('progress-text').textContent = statusText;
    document.getElementById('current-file-status').textContent = statusText;
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
