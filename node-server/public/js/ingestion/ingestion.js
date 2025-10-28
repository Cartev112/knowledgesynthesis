/**
 * Ingestion Manager - Handles document upload and knowledge extraction
 */
import { API } from '../utils/api.js';
import { state } from '../state.js';
import { showMessage } from '../utils/helpers.js';

export class IngestionManager {
  constructor() {
    this.contextConfig = {
      enabled: false,
      sources: {
        selectedNodes: false,
        selectedEdges: false,
        filteredView: false,
        documents: false,
        documentIds: []
      },
      intents: {
        complements: true,
        conflicts: true,
        extends: true,
        distinct: false
      }
    };
  }
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
  
  openContextConfig() {
    const modal = document.getElementById('context-config-modal');
    if (!modal) return;
    
    // Update counts
    document.getElementById('context-node-count').textContent = state.selectedNodes.size;
    document.getElementById('context-edge-count').textContent = state.selectedEdges?.size || 0;
    
    // Load documents list if needed
    this.loadDocumentsList();
    
    // Show modal
    modal.classList.add('visible');
    document.body.classList.add('modal-open');
    
    // Update summary
    this.updateContextSummary();
  }
  
  closeContextConfig() {
    const modal = document.getElementById('context-config-modal');
    if (modal) {
      modal.classList.remove('visible');
      document.body.classList.remove('modal-open');
    }
  }
  
  async loadDocumentsList() {
    try {
      const response = await fetch('/api/query/documents');
      if (!response.ok) return;
      
      const documents = await response.json();
      const listEl = document.getElementById('context-document-list');
      
      if (documents.length === 0) {
        listEl.innerHTML = '<div style="color: #9ca3af; font-style: italic;">No documents available</div>';
        return;
      }
      
      listEl.innerHTML = documents.map(doc => `
        <label class="checkbox-label" style="padding: 8px; margin: 4px 0; background: white; border-radius: 4px; cursor: pointer;">
          <input type="checkbox" class="checkbox-input context-doc-checkbox" data-doc-id="${doc.document_id}" />
          <span class="checkbox-text" style="font-size: 13px;">${doc.title || doc.document_id}</span>
        </label>
      `).join('');
      
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  }
  
  updateContextSummary() {
    const useNodes = document.getElementById('context-use-selected-nodes')?.checked;
    const useEdges = document.getElementById('context-use-selected-edges')?.checked;
    const useFiltered = document.getElementById('context-use-filtered-view')?.checked;
    const useDocs = document.getElementById('context-use-documents')?.checked;
    
    // Show/hide document selection
    const docSelection = document.getElementById('context-document-selection');
    if (docSelection) {
      docSelection.style.display = useDocs ? 'block' : 'none';
    }
    
    // Build summary
    const parts = [];
    if (useNodes && state.selectedNodes.size > 0) {
      parts.push(`${state.selectedNodes.size} concept(s)`);
    }
    if (useEdges && state.selectedEdges?.size > 0) {
      parts.push(`${state.selectedEdges.size} relationship(s)`);
    }
    if (useFiltered) {
      parts.push('filtered view');
    }
    if (useDocs) {
      const checked = document.querySelectorAll('.context-doc-checkbox:checked').length;
      if (checked > 0) parts.push(`${checked} document(s)`);
    }
    
    const detailsEl = document.getElementById('context-preview-details');
    if (detailsEl) {
      if (parts.length === 0) {
        detailsEl.textContent = 'No context configured yet';
      } else {
        detailsEl.innerHTML = `
          <div style="margin-bottom: 8px;"><strong>Sources:</strong> ${parts.join(', ')}</div>
          <div><strong>Intents:</strong> ${this.getSelectedIntents().join(', ') || 'Neutral (no specific intent)'}</div>
        `;
      }
    }
  }
  
  getSelectedIntents() {
    const intents = [];
    if (document.getElementById('intent-complements')?.checked) intents.push('Complement');
    if (document.getElementById('intent-conflicts')?.checked) intents.push('Conflict');
    if (document.getElementById('intent-extends')?.checked) intents.push('Extend');
    if (document.getElementById('intent-distinct')?.checked) intents.push('Distinct');
    return intents;
  }
  
  applyContextConfig() {
    // Save configuration
    this.contextConfig.enabled = true;
    this.contextConfig.sources.selectedNodes = document.getElementById('context-use-selected-nodes')?.checked || false;
    this.contextConfig.sources.selectedEdges = document.getElementById('context-use-selected-edges')?.checked || false;
    this.contextConfig.sources.filteredView = document.getElementById('context-use-filtered-view')?.checked || false;
    this.contextConfig.sources.documents = document.getElementById('context-use-documents')?.checked || false;
    
    // Get selected document IDs
    this.contextConfig.sources.documentIds = Array.from(
      document.querySelectorAll('.context-doc-checkbox:checked')
    ).map(cb => cb.dataset.docId);
    
    // Save intents
    this.contextConfig.intents.complements = document.getElementById('intent-complements')?.checked || false;
    this.contextConfig.intents.conflicts = document.getElementById('intent-conflicts')?.checked || false;
    this.contextConfig.intents.extends = document.getElementById('intent-extends')?.checked || false;
    this.contextConfig.intents.distinct = document.getElementById('intent-distinct')?.checked || false;
    
    // Update main UI summary
    this.updateMainContextSummary();
    
    // Close modal
    this.closeContextConfig();
    
    showMessage('success', 'Context configuration applied');
  }
  
  updateMainContextSummary() {
    const summaryEl = document.getElementById('context-summary-text');
    if (!summaryEl) return;
    
    if (!this.contextConfig.enabled) {
      summaryEl.innerHTML = 'No context configured';
      summaryEl.style.color = '#9ca3af';
      return;
    }
    
    const parts = [];
    if (this.contextConfig.sources.selectedNodes && state.selectedNodes.size > 0) {
      parts.push(`${state.selectedNodes.size} concepts`);
    }
    if (this.contextConfig.sources.selectedEdges && state.selectedEdges?.size > 0) {
      parts.push(`${state.selectedEdges.size} relationships`);
    }
    if (this.contextConfig.sources.filteredView) {
      parts.push('filtered view');
    }
    if (this.contextConfig.sources.documents && this.contextConfig.sources.documentIds.length > 0) {
      parts.push(`${this.contextConfig.sources.documentIds.length} docs`);
    }
    
    const intents = this.getActiveIntents();
    
    if (parts.length === 0) {
      summaryEl.innerHTML = '<span style="color: #ef4444;">⚠ Context enabled but no sources selected</span>';
    } else {
      summaryEl.innerHTML = `
        <div style="color: #059669; font-weight: 600; margin-bottom: 4px;">✓ Context Active</div>
        <div style="font-size: 12px; color: #6b7280;">${parts.join(', ')} • ${intents}</div>
      `;
    }
  }
  
  getActiveIntents() {
    const intents = [];
    if (this.contextConfig.intents.complements) intents.push('complement');
    if (this.contextConfig.intents.conflicts) intents.push('conflict');
    if (this.contextConfig.intents.extends) intents.push('extend');
    if (this.contextConfig.intents.distinct) intents.push('distinct');
    return intents.length > 0 ? intents.join(', ') : 'neutral';
  }
  
  clearContext() {
    this.contextConfig.enabled = false;
    this.contextConfig.sources = {
      selectedNodes: false,
      selectedEdges: false,
      filteredView: false,
      documents: false,
      documentIds: []
    };
    this.updateMainContextSummary();
    this.closeContextConfig();
    showMessage('success', 'Context cleared');
  }
  
  showDetailedContextPreview() {
    // Show the existing detailed preview modal
    this.showContextPreview();
  }
  
  async getGraphContextText() {
    if (!this.contextConfig.enabled) {
      return null;
    }
    
    // Check if any sources are configured
    const hasNodes = this.contextConfig.sources.selectedNodes && state.selectedNodes.size > 0;
    const hasEdges = this.contextConfig.sources.selectedEdges && state.selectedEdges?.size > 0;
    const hasFiltered = this.contextConfig.sources.filteredView;
    const hasDocs = this.contextConfig.sources.documents && this.contextConfig.sources.documentIds.length > 0;
    
    if (!hasNodes && !hasEdges && !hasFiltered && !hasDocs) {
      return null;
    }
    
    try {
      let allNodes = new Map();
      let allRelationships = new Map();
      let selectedRelationships = [];
      
      // Collect nodes from selected nodes
      if (hasNodes && state.selectedNodes.size > 0) {
        const nodeIds = Array.from(state.selectedNodes);
        const data = await API.getSubgraph(nodeIds);
        
        data.nodes.forEach(node => allNodes.set(node.id, node));
        data.relationships.forEach(rel => allRelationships.set(rel.id, rel));
      }
      
      // Collect nodes and relationships from selected edges
      if (hasEdges && state.selectedEdges.size > 0) {
        const edgeIds = Array.from(state.selectedEdges);
        
        // Get edge data from cytoscape
        if (state.cy) {
          edgeIds.forEach(edgeId => {
            const edge = state.cy.getElementById(edgeId);
            if (edge.length > 0) {
              const edgeData = edge.data();
              
              // Add the relationship
              selectedRelationships.push(edgeData);
              allRelationships.set(edgeId, edgeData);
              
              // Add source and target nodes
              const sourceNode = state.cy.getElementById(edgeData.source);
              const targetNode = state.cy.getElementById(edgeData.target);
              
              if (sourceNode.length > 0) {
                allNodes.set(edgeData.source, sourceNode.data());
              }
              if (targetNode.length > 0) {
                allNodes.set(edgeData.target, targetNode.data());
              }
            }
          });
        }
      }
      
      // Collect nodes and relationships from selected documents
      if (hasDocs && this.contextConfig.sources.documentIds.length > 0) {
        for (const docId of this.contextConfig.sources.documentIds) {
          try {
            // Fetch all entities and relationships for this document
            const response = await fetch(`/api/query/graph_by_docs?doc_ids=${encodeURIComponent(docId)}`);
            if (response.ok) {
              const docData = await response.json();
              
              // Add all nodes from this document
              if (docData.nodes) {
                docData.nodes.forEach(node => allNodes.set(node.id, node));
              }
              
              // Add all relationships from this document
              if (docData.relationships) {
                docData.relationships.forEach(rel => allRelationships.set(rel.id, rel));
              }
            }
          } catch (error) {
            console.error(`Error fetching document ${docId}:`, error);
          }
        }
      }
      
      // Handle filtered view - use currently visible graph
      if (hasFiltered && state.cy) {
        // Get all visible nodes and edges from cytoscape
        const visibleNodes = state.cy.nodes(':visible');
        const visibleEdges = state.cy.edges(':visible');
        
        visibleNodes.forEach(node => {
          allNodes.set(node.id(), node.data());
        });
        
        visibleEdges.forEach(edge => {
          allRelationships.set(edge.id(), edge.data());
        });
      }
      
      const nodes = Array.from(allNodes.values());
      const relationships = Array.from(allRelationships.values());
      
      // Get 1-hop neighbors for richer context
      const neighbors = this._getNeighbors(nodes, relationships);
      
      // Build intent instruction
      const intentInstructions = this.buildIntentInstructions();
      
      let contextText = '=== EXISTING KNOWLEDGE GRAPH CONTEXT ===\n\n';
      contextText += intentInstructions;
      contextText += `\nThis context contains ${nodes.length} concepts, ${neighbors.length} neighbor concepts, and ${relationships.length} relationships:\n\n`;
      
      // Highlight selected relationships if any
      if (selectedRelationships.length > 0) {
        contextText += 'SELECTED RELATIONSHIPS (Focus on these):\n';
        selectedRelationships.forEach(rel => {
          const sourceNode = allNodes.get(rel.source) || neighbors.find(n => n.id === rel.source);
          const targetNode = allNodes.get(rel.target) || neighbors.find(n => n.id === rel.target);
          const sourceName = String(sourceNode ? sourceNode.label : rel.source).replace(/[^\w\s-]/g, '');
          const targetName = String(targetNode ? targetNode.label : rel.target).replace(/[^\w\s-]/g, '');
          const relation = String(rel.relation || 'RELATED_TO').replace(/[^\w\s-]/g, '');
          const conf = rel.confidence ? ` (confidence: ${rel.confidence.toFixed(2)})` : '';
          const evidence = rel.original_text ? `\n  Evidence: "${rel.original_text.substring(0, 100)}..."` : '';
          
          contextText += `- ${sourceName} -> [${relation}] -> ${targetName}${conf}${evidence}\n`;
        });
        contextText += '\n';
      }
      
      contextText += 'SELECTED CONCEPTS:\n';
      nodes.forEach(node => {
        const label = String(node.label || 'Unknown').replace(/[^\w\s-]/g, '');
        const type = String(node.type || 'Concept').replace(/[^\w\s-]/g, '');
        const sig = node.significance ? ` (significance: ${node.significance}/5)` : '';
        contextText += `- ${label} (${type})${sig}\n`;
      });
      
      if (neighbors.length > 0) {
        contextText += '\nNEIGHBOR CONCEPTS:\n';
        neighbors.forEach(node => {
          const label = String(node.label || 'Unknown').replace(/[^\w\s-]/g, '');
          const type = String(node.type || 'Concept').replace(/[^\w\s-]/g, '');
          contextText += `- ${label} (${type})\n`;
        });
      }
      
      contextText += '\nALL RELATIONSHIPS:\n';
      relationships.forEach(rel => {
        const sourceNode = allNodes.get(rel.source) || neighbors.find(n => n.id === rel.source);
        const targetNode = allNodes.get(rel.target) || neighbors.find(n => n.id === rel.target);
        const sourceName = String(sourceNode ? sourceNode.label : rel.source).replace(/[^\w\s-]/g, '');
        const targetName = String(targetNode ? targetNode.label : rel.target).replace(/[^\w\s-]/g, '');
        const relation = String(rel.relation || 'RELATED_TO').replace(/[^\w\s-]/g, '');
        const conf = rel.confidence ? ` (confidence: ${rel.confidence.toFixed(2)})` : '';
        
        contextText += `- ${sourceName} -> [${relation}] -> ${targetName}${conf}\n`;
      });
      
      contextText += '\n=== END CONTEXT ===\n\n';
      return { text: contextText, data: { nodes, relationships }, neighbors };
      
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
      modal.classList.add('visible');
      
    } catch (error) {
      console.error('Error showing context preview:', error);
      alert('Error loading context preview');
    }
  }
  
  closeContextPreview() {
    const modal = document.getElementById('context-preview-modal');
    if (modal) {
      modal.classList.remove('visible');
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
  
  buildIntentInstructions() {
    const intents = [];
    if (this.contextConfig.intents.complements) {
      intents.push('- COMPLEMENT: Find relationships that support, confirm, or align with the existing knowledge');
    }
    if (this.contextConfig.intents.conflicts) {
      intents.push('- CONFLICT: Find relationships that contradict or disagree with the existing knowledge');
    }
    if (this.contextConfig.intents.extends) {
      intents.push('- EXTEND: Find new relationships that add to or expand upon the existing knowledge');
    }
    if (this.contextConfig.intents.distinct) {
      intents.push('- DISTINCT: Find relationships that are unrelated to the existing knowledge');
    }
    
    if (intents.length === 0) {
      return 'EXTRACTION INTENT: Neutral - extract all relevant relationships\n';
    }
    
    return 'EXTRACTION INTENT:\n' + intents.join('\n') + '\n';
  }
  
  async ingestDocument() {
    const pdfFiles = document.getElementById('pdf-file').files;
    const text = document.getElementById('text-input').value.trim();
    let extractionContext = document.getElementById('extraction-context').value.trim();
    const maxConcepts = parseInt(document.getElementById('max-concepts').value);
    const maxRelationships = parseInt(document.getElementById('max-relationships').value);
    const model = document.getElementById('model-select').value;
    const useGraphContext = this.contextConfig.enabled;
    
    if (pdfFiles.length === 0 && !text) {
      this.showStatus('error', 'Please upload PDF file(s) or paste text');
      return;
    }
    
    // Get graph context if enabled
    if (useGraphContext) {
      const result = await this.getGraphContextText();
      if (result && result.text) {
        if (extractionContext) {
          extractionContext = result.text + '\nUSER FOCUS: ' + extractionContext;
        } else {
          extractionContext = result.text;
        }
      } else {
        this.showStatus('error', 'Failed to load graph context. Please configure context sources.');
        return;
      }
    }

    // Append advanced configuration prompt if non-default settings
    const advancedPrompt = this.getAdvancedConfigPrompt();
    if (advancedPrompt && advancedPrompt.trim().length > 50) { // Only if there are actual additions
      if (extractionContext) {
        extractionContext = extractionContext + advancedPrompt;
      } else {
        extractionContext = advancedPrompt;
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
      modal.classList.add('visible');
    } else {
      modal.classList.remove('visible');
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

  openAdvancedConfig() {
    const modal = document.getElementById('advanced-extraction-modal-overlay');
    if (modal) {
      modal.classList.add('visible');
      document.body.classList.add('modal-open');
    }
  }

  closeAdvancedConfig() {
    const modal = document.getElementById('advanced-extraction-modal-overlay');
    if (modal) {
      modal.classList.remove('visible');
      document.body.classList.remove('modal-open');
    }
  }

  resetAdvancedConfig() {
    document.getElementById('extraction-density').value = 'balanced';
    document.getElementById('entity-granularity').value = 'balanced';
    document.getElementById('relationship-specificity').value = 'balanced';
    document.getElementById('temporal-context').value = 'ignore';
    document.getElementById('confidence-threshold').value = 'balanced';
    // Newly added parameters
    const pol = document.getElementById('polarity-emphasis'); if (pol) pol.value = 'balanced';
    const ev = document.getElementById('evidence-style'); if (ev) ev.value = 'balanced';
    const norm = document.getElementById('normalization-strictness'); if (norm) norm.value = 'balanced';
    const nov = document.getElementById('novelty-preference'); if (nov) nov.value = 'balanced';
    const caus = document.getElementById('causality-bias'); if (caus) caus.value = 'balanced';
  }

  getAdvancedConfigPrompt() {
    const density = document.getElementById('extraction-density')?.value || 'balanced';
    const granularity = document.getElementById('entity-granularity')?.value || 'balanced';
    const specificity = document.getElementById('relationship-specificity')?.value || 'balanced';
    const temporal = document.getElementById('temporal-context')?.value || 'ignore';
    const confidence = document.getElementById('confidence-threshold')?.value || 'balanced';
    const polarity = document.getElementById('polarity-emphasis')?.value || 'balanced';
    const evidenceStyle = document.getElementById('evidence-style')?.value || 'balanced';
    const normalization = document.getElementById('normalization-strictness')?.value || 'balanced';
    const novelty = document.getElementById('novelty-preference')?.value || 'balanced';
    const causality = document.getElementById('causality-bias')?.value || 'balanced';

    let promptAdditions = '';
    let hasAdditions = false;

    // Extraction Density
    if (density === 'comprehensive') {
      promptAdditions += 'EXTRACTION DENSITY: Comprehensive Network Mode\n';
      promptAdditions += '- Extract a DENSE, INTERCONNECTED knowledge network\n';
      promptAdditions += '- Include intermediate entities and multi-hop relationships\n';
      promptAdditions += '- Capture supporting details and contextual connections\n';
      promptAdditions += '- Aim for rich, graph-like structures with high connectivity\n\n';
      hasAdditions = true;
    } else if (density === 'focused') {
      promptAdditions += 'EXTRACTION DENSITY: Focused Triplets Mode\n';
      promptAdditions += '- Extract ONLY the most significant, direct relationships\n';
      promptAdditions += '- Focus on key entities and primary connections\n';
      promptAdditions += '- Omit intermediate or supporting details\n';
      promptAdditions += '- Prioritize quality over quantity\n\n';
      hasAdditions = true;
    }

    // Entity Granularity
    if (granularity === 'fine') {
      promptAdditions += 'ENTITY GRANULARITY: Fine-grained\n';
      promptAdditions += '- Use SPECIFIC, DETAILED entity names\n';
      promptAdditions += '- Include subtypes, variants, and specific forms (e.g., "BRAF V600E mutation", "CD8+ T cells")\n';
      promptAdditions += '- Preserve technical details and precision\n\n';
      hasAdditions = true;
    } else if (granularity === 'coarse') {
      promptAdditions += 'ENTITY GRANULARITY: Coarse-grained\n';
      promptAdditions += '- Use BROAD, GENERAL entity names\n';
      promptAdditions += '- Group specific variants into broader categories (e.g., "BRAF mutations", "T cells")\n';
      promptAdditions += '- Favor conceptual groupings over specific instances\n\n';
      hasAdditions = true;
    }

    // Relationship Specificity
    if (specificity === 'specific') {
      promptAdditions += 'RELATIONSHIP SPECIFICITY: Specific Predicates\n';
      promptAdditions += '- Use PRECISE, TECHNICAL predicates\n';
      promptAdditions += '- Examples: "phosphorylates", "upregulates", "competitively_inhibits", "binds_to_active_site"\n';
      promptAdditions += '- Capture the exact mechanism or nature of the relationship\n\n';
      hasAdditions = true;
    } else if (specificity === 'general') {
      promptAdditions += 'RELATIONSHIP SPECIFICITY: General Predicates\n';
      promptAdditions += '- Use BROAD, HIGH-LEVEL predicates\n';
      promptAdditions += '- Examples: "affects", "relates_to", "modulates", "influences"\n';
      promptAdditions += '- Focus on the existence of relationships rather than precise mechanisms\n\n';
      hasAdditions = true;
    }

    // Temporal Context
    if (temporal === 'include') {
      promptAdditions += 'TEMPORAL CONTEXT: Include Temporal Markers\n';
      promptAdditions += '- Extract TIME-BASED relationships and sequences\n';
      promptAdditions += '- Use temporal predicates: "occurs_before", "follows", "precedes", "triggers"\n';
      promptAdditions += '- Capture causal chains and temporal dependencies\n';
      promptAdditions += '- Note experimental timelines and progression\n\n';
      hasAdditions = true;
    }

    // Confidence Threshold
    if (confidence === 'high') {
      promptAdditions += 'CONFIDENCE THRESHOLD: High (Explicit Only)\n';
      promptAdditions += '- Extract ONLY explicitly stated relationships\n';
      promptAdditions += '- Require clear, direct evidence in the text\n';
      promptAdditions += '- Avoid inferring relationships from context\n';
      promptAdditions += '- Prioritize precision over recall\n\n';
      hasAdditions = true;
    } else if (confidence === 'permissive') {
      promptAdditions += 'CONFIDENCE THRESHOLD: Permissive (Include Inferred)\n';
      promptAdditions += '- Extract both explicit AND strongly implied relationships\n';
      promptAdditions += '- Use context and domain knowledge to infer connections\n';
      promptAdditions += '- Include relationships suggested by experimental design or discussion\n';
      promptAdditions += '- Prioritize recall over precision\n\n';
      hasAdditions = true;
    }

    // Relationship Polarity Emphasis
    if (polarity === 'negative') {
      promptAdditions += 'POLARITY EMPHASIS: Negative Findings\n';
      promptAdditions += '- Prefer extracting negative relationships when evidence exists (e.g., does_not_* predicates)\n';
      promptAdditions += '- Maintain representation of positive findings but favor negative outcomes if both are present\n\n';
      hasAdditions = true;
    } else if (polarity === 'positive') {
      promptAdditions += 'POLARITY EMPHASIS: Positive Findings\n';
      promptAdditions += '- Prefer extracting positive/affirmative relationships when evidence exists\n';
      promptAdditions += '- Still extract negative findings when they are central to the text\n\n';
      hasAdditions = true;
    }

    // Evidence Style
    if (evidenceStyle === 'verbatim') {
      promptAdditions += 'EVIDENCE STYLE: Verbatim Quotes\n';
      promptAdditions += "- For 'original_text', use direct sentence fragments quoted verbatim from the source\n";
      promptAdditions += "- Keep quotes concise but exact; include page cues if present\n\n";
      hasAdditions = true;
    } else if (evidenceStyle === 'summary') {
      promptAdditions += 'EVIDENCE STYLE: Summarized Evidence\n';
      promptAdditions += "- For 'original_text', provide a concise paraphrase capturing the exact claim\n";
      promptAdditions += "- Keep faithful to the source; avoid adding external information\n\n";
      hasAdditions = true;
    }

    // Normalization Strictness
    if (normalization === 'strict') {
      promptAdditions += 'NORMALIZATION: Strict Ontology Mapping\n';
      promptAdditions += "- Use canonical entity types and normalized, lowercase snake_case predicates\n";
      promptAdditions += "- Prefer controlled vocabulary; collapse synonymous predicates into a single canonical form\n\n";
      hasAdditions = true;
    } else if (normalization === 'natural') {
      promptAdditions += 'NORMALIZATION: Natural Language Friendly\n';
      promptAdditions += "- Still normalize to snake_case, but choose predicate terms that best preserve nuance\n";
      promptAdditions += "- Allow more expressive predicate choices when they add clarity\n\n";
      hasAdditions = true;
    }

    // Novelty Preference
    if (novelty === 'novel') {
      promptAdditions += 'NOVELTY PREFERENCE: Prefer Novel Findings\n';
      promptAdditions += "- Prioritize relationships that appear new, surprising, or explicitly described as novel\n";
      promptAdditions += "- Surface previously unreported connections highlighted by the text\n\n";
      hasAdditions = true;
    } else if (novelty === 'confirmatory') {
      promptAdditions += 'NOVELTY PREFERENCE: Prefer Confirmatory Findings\n';
      promptAdditions += "- Prioritize relationships that confirm or replicate known findings\n";
      promptAdditions += "- Emphasize consensus and reproducibility signals in the text\n\n";
      hasAdditions = true;
    }

    // Causality Bias
    if (causality === 'causal') {
      promptAdditions += 'CAUSALITY BIAS: Prefer Causal\n';
      promptAdditions += "- Prefer causal predicates (e.g., causes, increases, induces) when justified\n";
      promptAdditions += "- Only use associative predicates when causal interpretation is not supported\n\n";
      hasAdditions = true;
    } else if (causality === 'associative') {
      promptAdditions += 'CAUSALITY BIAS: Prefer Associative\n';
      promptAdditions += "- Prefer associative/correlative predicates (e.g., associated_with, correlates_with) unless causality is explicit\n";
      promptAdditions += "- Avoid overstating causality without clear evidence\n\n";
      hasAdditions = true;
    }

    if (!hasAdditions) return '';

    return '\n\n=== ADVANCED EXTRACTION PARAMETERS ===\n' + promptAdditions + '=== END ADVANCED PARAMETERS ===\n';
  }
}
