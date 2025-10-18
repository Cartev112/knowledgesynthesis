/**
 * Main Application Entry Point
 */
import { AuthManager } from './auth.js';
import { IngestionManager } from './ingestion/ingestion.js';
import { GraphViewer } from './viewing/graph-viewer.js';
import { QueryBuilder } from './query-builder/query-builder.js';
import { state } from './state.js';
import { API } from './utils/api.js';

class AppManager {
  constructor() {
    this.authManager = new AuthManager();
    this.ingestionManager = new IngestionManager();
    this.graphViewer = new GraphViewer();
    this.queryBuilder = new QueryBuilder();
    this.currentTab = 'ingestion';
  }
  
  async init() {
    console.log('Initializing Knowledge Synthesis Platform...');
    
    // Check authentication
    await this.authManager.checkAuth();
    
    // Load initial data
    await this.loadDocuments();
    
    // Wire global events
    this.wireGlobalEvents();
    
    console.log('Application initialized successfully');
  }
  
  async loadDocuments() {
    try {
      const data = await API.getDocuments();
      state.documents = data.documents || [];
    } catch (e) {
      console.error('Failed to load documents:', e);
    }
  }
  
  switchTab(tabName) {
    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    
    // Add active class to selected tab
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
      if (tab.textContent.toLowerCase().includes(tabName.replace('-', ' '))) {
        tab.classList.add('active');
      }
    });
    
    const contentElement = document.getElementById(`${tabName}-tab`);
    if (contentElement) contentElement.classList.add('active');
    
    this.currentTab = tabName;
    
    // Initialize tab-specific functionality
    if (tabName === 'viewing') {
      this.initViewingTab();
    } else if (tabName === 'query-builder') {
      this.initQueryBuilderTab();
    }
    
    // Update UI visibility
    this.updateUIVisibility(tabName);
  }
  
  async initViewingTab() {
    if (!state.graphInitialized) {
      console.log('Initializing graph viewer...');
      
      requestAnimationFrame(() => {
        this.graphViewer.init();
        setTimeout(async () => {
          if (state.cy) {
            state.cy.resize();
          }
          await this.graphViewer.loadAllData();
          state.graphInitialized = true;
        }, 150);
      });
    } else if (state.cy) {
      requestAnimationFrame(() => {
        state.cy.resize();
        state.cy.fit(undefined, 20);
      });
      setTimeout(() => {
        state.cy.resize();
      }, 100);
    }
  }
  
  async initQueryBuilderTab() {
    if (!window.queryBuilderInitialized) {
      await this.queryBuilder.init();
      window.queryBuilderInitialized = true;
    }
  }
  
  updateUIVisibility(tabName) {
    const indexToggleBtn = document.getElementById('index-toggle-btn');
    const legendToggleBtn = document.getElementById('legend-toggle-btn');
    const fabContainer = document.getElementById('fab-container');
    
    if (tabName === 'viewing') {
      if (indexToggleBtn) indexToggleBtn.style.display = 'flex';
      if (legendToggleBtn) legendToggleBtn.style.display = 'flex';
    } else {
      if (indexToggleBtn) indexToggleBtn.style.display = 'none';
      if (legendToggleBtn) legendToggleBtn.style.display = 'none';
      if (fabContainer) fabContainer.classList.add('hidden');
    }
  }
  
  wireGlobalEvents() {
    // ESC key handler
    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        if (state.selectedNodes && state.selectedNodes.size > 0) {
          this.graphViewer.clearSelection();
        }
        this.graphViewer.clearAllHighlights();
      }
    });
    
    // Window resize handler
    window.addEventListener('resize', () => {
      if (state.cy && this.currentTab === 'viewing') {
        state.cy.resize();
        state.cy.fit(undefined, 20);
      }
    });
  }
  
  // FAB Actions for 2-Node Selection
  createRelationship() {
    if (state.selectedNodes.size !== 2) {
      alert('Please select exactly 2 nodes');
      return;
    }
    
    const nodeIds = Array.from(state.selectedNodes);
    const node1 = state.cy.getElementById(nodeIds[0]);
    const node2 = state.cy.getElementById(nodeIds[1]);
    
    // Store nodes for relationship creation
    this.manualEdgeNodes = {
      node1: {
        id: node1.id(),
        label: node1.data('label')
      },
      node2: {
        id: node2.id(),
        label: node2.data('label')
      }
    };
    
    // Populate form
    document.getElementById('manual-from').value = this.manualEdgeNodes.node1.label;
    document.getElementById('manual-to').value = this.manualEdgeNodes.node2.label;
    
    // Show modal
    const modal = document.getElementById('create-edge-modal');
    if (modal) {
      modal.style.display = 'flex';
    }
  }
  
  closeCreateRelationshipModal() {
    const modal = document.getElementById('create-edge-modal');
    if (modal) {
      modal.style.display = 'none';
    }
    document.getElementById('create-edge-form').reset();
  }
  
  async saveManualRelationship(event) {
    event.preventDefault();
    
    const relation = document.getElementById('manual-relation').value;
    const evidence = document.getElementById('manual-evidence').value;
    const confidence = parseFloat(document.getElementById('manual-confidence').value);
    
    try {
      const payload = {
        subject_id: this.manualEdgeNodes.node1.id,
        subject_name: this.manualEdgeNodes.node1.label,
        object_id: this.manualEdgeNodes.node2.id,
        object_name: this.manualEdgeNodes.node2.label,
        relation: relation,
        evidence: evidence,
        confidence: confidence,
        created_by: state.currentUser?.email || 'expert-user',
        created_by_first_name: state.currentUser?.first_name || '',
        created_by_last_name: state.currentUser?.last_name || ''
      };
      
      const response = await fetch('/api/manual/relationship', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      if (!response.ok) {
        throw new Error('Failed to create relationship');
      }
      
      this.closeCreateRelationshipModal();
      this.graphViewer.clearSelection();
      alert('✓ Manual relationship created successfully!');
      
      // Reload the graph to show the new relationship
      await this.graphViewer.loadAllData();
    } catch (e) {
      alert('Error creating relationship: ' + e.message);
    }
  }
  
  findPathBetweenNodes() {
    if (state.selectedNodes.size !== 2) {
      alert('Please select exactly 2 nodes');
      return;
    }
    
    const nodeIds = Array.from(state.selectedNodes);
    console.log('Finding path between:', nodeIds);
    
    // TODO: Implement pathfinding algorithm
    alert('Path finding feature coming soon!');
  }
  
  compareNodes() {
    if (state.selectedNodes.size !== 2) {
      alert('Please select exactly 2 nodes');
      return;
    }
    
    const nodeIds = Array.from(state.selectedNodes);
    console.log('Comparing nodes:', nodeIds);
    
    // TODO: Implement node comparison modal
    alert('Node comparison feature coming soon!');
  }
  
  mergeNodes() {
    if (state.selectedNodes.size !== 2) {
      alert('Please select exactly 2 nodes');
      return;
    }
    
    const nodeIds = Array.from(state.selectedNodes);
    console.log('Merging nodes:', nodeIds);
    
    // TODO: Implement node merging
    alert('Node merging feature coming soon!');
  }
}

// Initialize application
const appManager = new AppManager();
appManager.init().catch(err => {
  console.error('Failed to initialize application:', err);
});

// Expose to window for inline onclick handlers
window.appManager = appManager;
window.authManager = appManager.authManager;
window.ingestionManager = appManager.ingestionManager;
window.viewingManager = appManager.graphViewer;
window.queryBuilderManager = appManager.queryBuilder;

// Expose specific functions for HTML onclick handlers
window.toggleIndex = () => appManager.graphViewer.toggleIndex();
window.toggleLegend = () => appManager.graphViewer.toggleLegend();
window.closeLegendModal = () => appManager.graphViewer.toggleLegend();
window.filterIndex = () => appManager.graphViewer.indexManager.renderIndexItems();
window.closeEdgeModal = () => {
  const modal = document.getElementById('edge-modal-overlay');
  if (modal) modal.classList.remove('visible');
};
window.closeNodeModal = () => {
  const modal = document.getElementById('node-modal-overlay');
  if (modal) modal.classList.remove('visible');
};
window.closeDocumentModal = () => {
  const modal = document.getElementById('document-modal-overlay');
  if (modal) modal.classList.remove('visible');
};
