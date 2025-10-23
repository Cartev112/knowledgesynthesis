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
    // 3D viewer state (lazy-loaded)
    this.graph3D = null;
    this.is3D = false;
    this._graphDataFor3D = null;
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
      // Reload graph data to show newly ingested documents
      console.log('Reloading graph data...');
      await this.graphViewer.loadAllData();
      
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
      if (indexToggleBtn) indexToggleBtn.classList.remove('hidden');
      if (legendToggleBtn) legendToggleBtn.classList.remove('hidden');
    } else {
      if (indexToggleBtn) indexToggleBtn.classList.add('hidden');
      if (legendToggleBtn) legendToggleBtn.classList.add('hidden');
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
        // 3D: reset view and hide tooltip
        if (this.is3D && this.graph3D) {
          this.graph3D.resetView();
          const tip = document.getElementById('node-tooltip');
          if (tip) tip.classList.remove('visible');
        } else if (state.cy) {
          // 2D: reset zoom/fit
          state.cy.fit(undefined, 20);
        }
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
  
  async toggle3D() {
    // Ensure we're on the viewing tab
    if (this.currentTab !== 'viewing') {
      this.switchTab('viewing');
    }

    const cyEl = document.getElementById('cy');
    const container3d = document.getElementById('graph3d-container');
    const ui3d = document.getElementById('graph3d-ui');
    if (!cyEl || !container3d) return;

    // Toggling to 3D
    if (!this.is3D) {
      cyEl.classList.add('hidden');
      container3d.classList.remove('hidden');
      if (ui3d) ui3d.classList.remove('hidden');
      // Hide 2D tooltips if visible
      const edgeTip = document.getElementById('edge-tooltip');
      const nodeTip = document.getElementById('node-tooltip');
      if (edgeTip) edgeTip.classList.add('hidden');
      if (nodeTip) nodeTip.classList.add('hidden');

      // Lazy load Graph3D controller
      if (!this.graph3D) {
        const mod = await import('./viewing/graph3d/graph3d-controller.js');
        this.graph3D = mod.initGraph3D(container3d, null, { render: { fogEnabled: true } });
        // Expose simple controls once
        if (!window.toggle3DFog) window.toggle3DFog = () => this.graph3D.toggleFog();
        if (!window.set3DPointSize) window.set3DPointSize = (s) => this.graph3D.setPointSize(Number(s));
        if (!window.toggle3DLayout) window.toggle3DLayout = () => this.graph3D.toggleForceLayout();
        if (!window.reset3DLayout) window.reset3DLayout = () => this.graph3D.resetLayout();
        // Route 2D selection events into 3D
        window.onSelectionChanged = (ids) => {
          if (this.graph3D) this.graph3D.applySelection(ids);
        };
      }

      // Load data once for 3D (paginate like 2D)
      if (!this._graphDataFor3D) {
        try {
          const pageSize = 1000;
          let page = 1;
          const nodesMap = new Map();
          const relsMap = new Map();
          while (true) {
            const data = await API.getAllGraph(pageSize, page);
            const nodes = data.nodes || [];
            const rels = data.relationships || [];
            nodes.forEach(n => nodesMap.set(n.id, n));
            rels.forEach(r => relsMap.set(r.id, r));
            if (nodes.length < pageSize) break;
            page++;
          }
          this._graphDataFor3D = {
            nodes: Array.from(nodesMap.values()),
            relationships: Array.from(relsMap.values())
          };
        } catch (e) {
          console.error('Failed to load graph data for 3D:', e);
        }
      }

      if (this._graphDataFor3D) {
        this.graph3D.setData(this._graphDataFor3D);
        // Apply current 2D selection into 3D on first load
        if (state.selectedNodes && state.selectedNodes.size > 0) {
          this.graph3D.applySelection(Array.from(state.selectedNodes));
        }
      }

      this.is3D = true;
    } else {
      // Back to 2D
      container3d.classList.add('hidden');
      cyEl.classList.remove('hidden');
      if (ui3d) ui3d.classList.add('hidden');
      this.is3D = false;
      if (state.cy) {
        requestAnimationFrame(() => {
          state.cy.resize();
          state.cy.fit(undefined, 20);
        });
      }
    }
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
      modal.classList.add('visible');
    }
  }
  
  closeCreateRelationshipModal() {
    const modal = document.getElementById('create-edge-modal');
    if (modal) {
      modal.classList.remove('visible');
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
  
  openExport() {
    // Export current graph to various formats
    const elements = state.cy.elements().jsons();
    const exportData = {
      nodes: elements.filter(e => e.group === 'nodes'),
      edges: elements.filter(e => e.group === 'edges')
    };
    
    // Create download options modal
    const formats = ['JSON', 'CSV', 'GraphML'];
    const format = prompt(`Export format:\n1. JSON\n2. CSV (nodes and edges)\n3. GraphML\n\nEnter 1, 2, or 3:`);
    
    if (format === '1') {
      // JSON export
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `knowledge-graph-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } else if (format === '2') {
      // CSV export (simplified)
      alert('CSV export coming soon!');
    } else if (format === '3') {
      // GraphML export
      alert('GraphML export coming soon!');
    }
  }
  
  openReviewQueue() {
    // Navigate to review queue page
    window.location.href = '/review-ui';
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
window.getSelectedNodeCount = () => state.selectedNodes?.size || 0;

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
  if (modal) {
    modal.classList.remove('visible');
    // Reset pagination when closing
    if (window.viewingManager && window.viewingManager.modalManager) {
      window.viewingManager.modalManager.resetDocModalPagination();
    }
  }
};

// 3D toggle
window.toggle3D = () => appManager.toggle3D();
