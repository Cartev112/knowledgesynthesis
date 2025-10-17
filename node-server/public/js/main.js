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
