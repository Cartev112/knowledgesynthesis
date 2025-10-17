# Complete Setup Guide - Node Server Frontend

## Directory Structure to Create

```bash
cd node-server
mkdir -p public/{css,js/{ingestion,viewing,query-builder,utils},assets}
```

Result:
```
node-server/
├── server.js (updated - provided)
├── users.js (existing)
├── package.json (existing)
├── uploads/
└── public/
    ├── index.html (provided)
    ├── css/
    │   ├── base.css
    │   ├── ingestion.css
    │   ├── viewing.css
    │   ├── query-builder.css
    │   └── modals.css
    ├── js/
    │   ├── main.js
    │   ├── auth.js
    │   ├── state.js
    │   ├── ingestion/
    │   │   └── ingestion.js
    │   ├── viewing/
    │   │   ├── graph-viewer.js
    │   │   ├── cytoscape-manager.js
    │   │   ├── index-panel.js
    │   │   └── modals.js
    │   ├── query-builder/
    │   │   └── query-builder.js
    │   └── utils/
    │       ├── api.js
    │       └── helpers.js
    └── assets/
```

## Step 1: Update server.js

Replace your current `node-server/server.js` with the updated version provided.

Key changes:
- Serves static files from `/static` prefix
- Proxies `/api/*` requests to Python FastAPI backend
- Main app served at `/` and `/app`
- Authentication integrated with session management

## Step 2: Create HTML file

Save the provided `index.html` to `node-server/public/index.html`

## Step 3: Extract CSS Files

### `public/css/base.css`

From the original main_ui.py, extract lines 20-350 (approximately):

```css
/* Base Styles */
* { box-sizing: border-box; }
html, body { 
  height: 100%; 
  margin: 0; 
  padding: 0; 
  font-family: system-ui, -apple-system, sans-serif; 
}

#header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

#header h1 { 
  margin: 0; 
  font-size: 24px; 
  font-weight: 600; 
}

/* User Info */
#user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  color: rgba(255,255,255,0.95);
}

#user-info button {
  background: rgba(255,255,255,0.2);
  color: white;
  border: 1px solid rgba(255,255,255,0.3);
  padding: 6px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

#user-info button:hover { 
  background: rgba(255,255,255,0.3); 
}

/* Tab Navigation */
#tabs {
  display: flex;
  background: #f3f4f6;
  border-bottom: 2px solid #e5e7eb;
  padding: 0 24px;
}

.tab {
  padding: 14px 24px;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  font-weight: 500;
  color: #6b7280;
  transition: all 0.2s;
}

.tab:hover { color: #374151; }
.tab.active { 
  color: #667eea; 
  border-bottom-color: #667eea; 
  background: white; 
}

.tab-content {
  display: none;
  height: calc(100vh - 120px);
  overflow: hidden;
}

.tab-content.active { 
  display: block; 
}

/* Card */
.card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px 28px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  width: 100%;
}

.card h2 {
  margin: 0 0 20px 0;
  font-size: 20px;
  color: #111827;
  border-bottom: 2px solid #667eea;
  padding-bottom: 10px;
}

/* Form Elements */
.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 6px;
  color: #374151;
}

.form-group .help-text {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

input[type="file"],
input[type="number"],
input[type="text"],
textarea,
select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
}

textarea {
  resize: vertical;
  min-height: 100px;
}

button.primary {
  background: #667eea;
  color: white;
  border: none;
  padding: 12px 32px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

button.primary:hover { 
  background: #5568d3; 
}

button.primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

/* Status Badges */
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.status-unverified { 
  background: #fef3c7; 
  color: #92400e; 
}

.status-verified { 
  background: #d1fae5; 
  color: #065f46; 
}

.status-incorrect { 
  background: #fee2e2; 
  color: #991b1b; 
}
```

### `public/css/ingestion.css`

```css
/* Ingestion Tab */
#ingestion-panel {
  max-width: 1400px;
  margin: 20px auto;
  padding: 0 24px;
  height: calc(100vh - 180px);
  display: flex;
  align-items: center;
}

.ingestion-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}

.custom-file-upload {
  display: inline-block;
  padding: 14px 28px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff !important;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  text-align: center;
  transition: all 0.3s;
  box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
}

.custom-file-upload:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
}

input[type="file"] {
  display: none;
}

.file-name-display {
  margin-top: 10px;
  padding: 10px 12px;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 13px;
  color: #374151;
  min-height: 40px;
  display: flex;
  align-items: center;
}

/* Progress Bar */
.progress-container {
  margin-top: 8px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  display: none;
}

.progress-container.active {
  display: block;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  color: #374151;
  font-weight: 600;
}

.progress-bar-bg {
  width: 100%;
  height: 24px;
  background: #e5e7eb;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  font-weight: 600;
}

/* Status Messages */
#ingest-status {
  margin-top: 12px;
  padding: 12px;
  border-radius: 6px;
  display: none;
  font-size: 13px;
}

#ingest-status.success {
  display: block;
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #6ee7b7;
}

#ingest-status.error {
  display: block;
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

#ingest-status.processing {
  display: block;
  background: #dbeafe;
  color: #1e40af;
  border: 1px solid #93c5fd;
}
```

### `public/css/viewing.css`

```css
/* Viewing Tab */
#viewing-panel {
  position: relative;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

#cy-container {
  position: relative;
  background: #fafafa;
  overflow: hidden;
  height: 100%;
  width: 100%;
}

#cy { 
  width: 100%; 
  height: 100%;
}

/* Index Panel */
#index-panel {
  position: fixed;
  right: 0;
  top: 115px;
  bottom: 0;
  width: 320px;
  background: white;
  border-left: 2px solid #e5e7eb;
  box-shadow: -4px 0 12px rgba(0,0,0,0.05);
  overflow-y: auto;
  padding: 20px;
  z-index: 100;
  transition: transform 0.3s ease;
}

#index-panel.hidden {
  transform: translateX(100%);
}

/* FABs */
.fab-container {
  position: fixed;
  bottom: 24px;
  left: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  z-index: 100;
}

.fab-container.hidden {
  display: none;
}

.fab {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(139, 92, 246, 0.5);
}

/* Toggle Buttons */
#index-toggle-btn,
#legend-toggle-btn {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  border: none;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
  cursor: pointer;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  transition: all 0.3s;
}

#legend-toggle-btn {
  right: 100px;
}
```

### `public/css/query-builder.css`

```css
/* Query Builder */
#query-builder-content {
  max-width: 1400px;
  margin: 20px auto;
  padding: 0 24px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  height: calc(100vh - 180px);
  overflow-y: auto;
}

.template-btn {
  width: 100%;
  padding: 12px 16px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  text-align: left;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
}

.template-btn:hover {
  border-color: #8b5cf6;
  background: #f5f3ff;
  color: #7c3aed;
}

.query-result-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s;
}

.query-result-card:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border-color: #8b5cf6;
}

#pattern-preview {
  background: #f9fafb;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  min-height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: monospace;
  font-size: 14px;
  color: #374151;
}
```

### `public/css/modals.css`

```css
/* Modal Overlays */
.modal-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 2000;
  align-items: center;
  justify-content: center;
}

.modal-overlay.visible {
  display: flex;
}

/* Modal Content */
.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 2px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  background: white;
  z-index: 1;
}

.modal-title {
  font-size: 20px;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.modal-close {
  background: transparent;
  border: none;
  font-size: 28px;
  cursor: pointer;
  color: #6b7280;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
}

.modal-close:hover {
  color: #111827;
}

.modal-body {
  padding: 24px;
}

/* Tooltips */
#edge-tooltip,
#node-tooltip {
  position: fixed;
  background: white;
  border: 2px solid #8b5cf6;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 1000;
  pointer-events: auto;
  display: none;
  max-width: 300px;
  font-size: 13px;
}

#edge-tooltip.visible,
#node-tooltip.visible {
  display: block;
}

/* Legend Modal */
#legend-modal-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1000;
  justify-content: center;
  align-items: center;
}

#legend-modal-overlay.visible {
  display: flex;
}

#legend-modal {
  background: white;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
}

.legend-section {
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 4px 0;
  color: #6b7280;
}
```

## Step 4: Create JavaScript Files

### `public/js/state.js`

```javascript
/**
 * Global Application State
 */
export const state = {
  currentUser: null,
  cy: null,
  selectedNodes: new Set(),
  manualEdgeNodes: { node1: null, node2: null },
  graphInitialized: false,
  indexVisible: false,
  activeDocuments: new Set(),
  indexData: { nodes: [], edges: [], documents: [] },
  viewportMode: false,
  isLoading: false,
  loadedNodes: new Set()
};
```

### `public/js/utils/api.js`

```javascript
/**
 * API Wrapper for Backend Communication
 */
export class API {
  static async request(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.message || `HTTP ${response.status}`);
    }
    
    return response.json();
  }
  
  static async get(url) {
    return this.request(url);
  }
  
  static async post(url, data) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  static async put(url, data) {
    return this.request(url, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }
  
  static async delete(url) {
    return this.request(url, {
      method: 'DELETE'
    });
  }
  
  // Specific API endpoints
  static async getCurrentUser() {
    return this.get('/api/me');
  }
  
  static async logout() {
    return this.post('/api/logout', {});
  }
  
  static async getDocuments() {
    return this.get('/query/documents');
  }
  
  static async getAllGraph() {
    const timestamp = new Date().getTime();
    return this.get(`/query/all?t=${timestamp}`);
  }
  
  static async searchConcept(name, verifiedOnly = false) {
    return this.get(`/query/search/concept?name=${encodeURIComponent(name)}&verified_only=${verifiedOnly}`);
  }
  
  static async getSubgraph(nodeIds) {
    return this.post('/query/subgraph', { node_ids: nodeIds });
  }
  
  static async ingestPDF(formData) {
    const response = await fetch('/ingest/pdf', {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to ingest PDF');
    }
    
    return response.json();
  }
  
  static async ingestText(data) {
    return this.post('/ingest/text', data);
  }
}
```

### `public/js/utils/helpers.js`

```javascript
/**
 * Utility Helper Functions
 */

export function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

export function showMessage(msg, type = 'success') {
  const messageEl = document.getElementById('message') || createMessageElement();
  messageEl.textContent = msg;
  messageEl.className = 'show';
  messageEl.style.background = type === 'error' ? '#dc2626' : type === 'warning' ? '#f59e0b' : '#10b981';
  setTimeout(() => messageEl.classList.remove('show'), 3000);
}

function createMessageElement() {
  const el = document.createElement('div');
  el.id = 'message';
  el.style.cssText = `
    position: fixed;
    top: 80px;
    right: 24px;
    padding: 12px 20px;
    border-radius: 6px;
    color: white;
    font-weight: 500;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    display: none;
    z-index: 1000;
  `;
  document.body.appendChild(el);
  return el;
}

export function formatDate(dateString) {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return date.toLocaleString();
}

export function debounce(fn, ms) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn.apply(this, args), ms);
  };
}
```

### `public/js/auth.js`

```javascript
/**
 * Authentication Manager
 */
import { API } from './utils/api.js';
import { state } from './state.js';

export class AuthManager {
  async checkAuth() {
    try {
      const data = await API.getCurrentUser();
      state.currentUser = data.user;
      const usernameEl = document.getElementById('username');
      if (usernameEl) {
        usernameEl.textContent = state.currentUser.username || state.currentUser.user_id || 'User';
      }
    } catch (e) {
      console.error('Auth check failed:', e);
      window.location.href = '/login';
    }
  }
  
  async logout() {
    try {
      await API.logout();
    } catch (e) {
      console.error('Logout failed:', e);
    }
    window.location.href = '/login';
  }
}
```

### `public/js/main.js` (Entry Point)

```javascript
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
    const tabElement = event?.target || document.querySelector(`[onclick*="${tabName}"]`);
    if (tabElement) tabElement.classList.add('active');
    
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
```

## Step 5: Create Remaining JavaScript Modules

Due to length constraints, here's the structure for remaining modules:

### `public/js/ingestion/ingestion.js`
- Extract all ingestion logic from main_ui.py
- Methods: `displayFileName()`, `toggleGraphContext()`, `getGraphContextText()`, `ingestDocument()`, `pollJobStatus()`, etc.

### `public/js/viewing/graph-viewer.js`
- Main viewing coordinator
- Methods: `init()`, `loadAllData()`, `toggleIndex()`, `toggleLegend()`, `clearSelection()`, etc.

### `public/js/viewing/cytoscape-manager.js`
- Cytoscape initialization and management
- Methods: `initCytoscape()`, `renderGraph()`, `wireEvents()`, etc.

### `public/js/viewing/index-panel.js`
- Index panel logic
- Methods: `populateIndex()`, `renderIndexItems()`, `toggleDocument()`, etc.

### `public/js/viewing/modals.js`
- Modal management
- Methods: `showEdgeTooltip()`, `showEdgeModal()`, `showNodeTooltip()`, `showNodeModal()`, etc.

### `public/js/query-builder/query-builder.js`
- Query builder logic
- Methods: `init()`, `loadGraphSchema()`, `executePatternQuery()`, `visualizeQueryResults()`, etc.

## Step 6: Update Python Backend

**IMPORTANT**: Since Node server now serves the frontend, update the Python route to just provide API:

In `backendAndUI/python_worker/app/routes/main_ui.py`:

```python
"""Main UI route - now redirects to Node server"""
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()

@router.get("")
def serve_main_ui():
    """Redirect to Node.js server for UI"""
    return RedirectResponse(url="http://127.0.0.1:3000/app")
```

## Step 7: Testing

1. **Start Python backend**: `uvicorn app.main:app --reload` (from python_worker directory)
2. **Start Node server**: `node server.js` (from node-server directory)
3. **Access app**: http://127.0.0.1:3000/
4. **Test all features**:
   - Authentication
   - Document upload
   - Graph visualization
   - Query builder
   - Review queue

## Architecture Benefits

✅ **Clear separation**: Node handles frontend, Python handles data processing
✅ **Better performance**: Static files served efficiently by Node
✅ **Easier development**: Frontend devs work in node-server, backend devs in python_worker
✅ **Scalability**: Can deploy Node and Python separately
✅ **Maintainability**: Small, focused files instead of one giant file

## Deployment Notes

For production:
1. Set environment variables properly
2. Use nginx/Apache to serve static files
3. Consider using a process manager (PM2 for Node)
4. Enable HTTPS
5. Configure CORS properly

# JavaScript Code Extraction Map

## From main_ui.py JavaScript Section (lines 876-2345)

### Extract to `public/js/ingestion/ingestion.js`

**Lines to extract**: Search for these function definitions in the original file:
- `function displayFileName()`
- `function toggleGraphContext()`
- `async function getGraphContextText()`
- `async function ingestDocument()`
- `async function pollJobStatus()`
- `function convertButtonToStatusBar()`
- `function updateStatusBar()`
- `function restoreButton()`
- `function showProgress()`
- `function updateProgress()`
- `function hideStatus()`
- `function showStatus()`

**Template**:
```javascript
import { API } from '../utils/api.js';
import { state } from '../state.js';
import { showMessage } from '../utils/helpers.js';

export class IngestionManager {
  displayFileName() {
    // Copy code from main_ui.py
  }
  
  toggleGraphContext() {
    // Copy code
  }
  
  async getGraphContextText() {
    // Copy code
  }
  
  async ingestDocument() {
    // Copy code - replace fetch() with API.post()
  }
  
  // ... other methods
}
```

### Extract to `public/js/viewing/cytoscape-manager.js`

**Lines to extract**:
- `function initCytoscape()`
- `function renderGraph(data)`
- `function toCytoscapeElements(graph)`
- `function runLayout()`
- All `cy.on()` event handlers

**Template**:
```javascript
import { state } from '../state.js';

export class CytoscapeManager {
  initCytoscape() {
    cytoscape.use(cytoscapeDagre);
    
    state.cy = cytoscape({
      container: document.getElementById('cy'),
      elements: [],
      wheelSensitivity: 0.2,
      // ... copy all config from main_ui.py
    });
    
    this.wireEvents();
  }
  
  wireEvents() {
    // Copy all cy.on() handlers
    state.cy.on('tap', 'node', (evt) => { /* ... */ });
    state.cy.on('tap', 'edge', (evt) => { /* ... */ });
    // etc.
  }
  
  renderGraph(data) {
    // Copy renderGraph() logic
  }
  
  toCytoscapeElements(graph) {
    // Copy conversion logic
  }
}
```

### Extract to `public/js/viewing/index-panel.js`

**Lines to extract**:
- `function toggleIndex()`
- `async function populateIndex()`
- `function renderIndexItems()`
- `function filterIndex()`
- `function highlightDocumentElements()`
- `function toggleDocument()`
- `function applyDocumentFilter()`
- `async function showDocumentModal()`
- `function closeDocumentModal()`

### Extract to `public/js/viewing/modals.js`

**Lines to extract**:
- `function showEdgeTooltip(edge, event)`
- `function hideEdgeTooltip()`
- `function showEdgeModal(data)`
- `function closeEdgeModal()`
- `function showNodeTooltip(node, event)`
- `function hideNodeTooltip()`
- `function showNodeModal(data)`
- `function closeNodeModal()`

### Extract to `public/js/viewing/graph-viewer.js`

**Lines to extract**:
- `async function loadAllData()`
- `async function loadDocuments()`
- `async function searchConcept()`
- `function highlightSearchResults(query)`
- `function clearSelection()`
- `function clearAllHighlights()`

### Extract to `public/js/query-builder/query-builder.js`

**Lines to extract**:
- `async function loadGraphSchema()`
- `function updatePatternPreview()`
- `async function executePatternQuery()`
- `function displayQueryResults(results)`
- `function clearQueryBuilder()`
- `function visualizeQueryResults()`

## Key Replacements to Make

### 1. Replace global variables with state imports
```javascript
// OLD (in main_ui.py)
let currentUser = null;
let cy = null;

// NEW (in your modules)
import { state } from './state.js';
// Use: state.currentUser, state.cy
```

### 2. Replace fetch() with API class
```javascript
// OLD
const res = await fetch('/api/endpoint', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
});

// NEW
import { API } from './utils/api.js';
const data = await API.post('/api/endpoint', data);
```

### 3. Replace direct DOM access with methods
```javascript
// OLD
document.getElementById('status').textContent = 'Loading...';

// NEW (if in a class)
updateStatus(message) {
  const statusEl = document.getElementById('status');
  if (statusEl) statusEl.textContent = message;
}
```

### 4. Export functions as class methods
```javascript
// OLD (global function)
function doSomething() { }

// NEW (class method)
export class MyManager {
  doSomething() { }
}
```

## Quick Start Command Sequence

```bash
cd node-server

# Create directory structure
mkdir -p public/{css,js/{ingestion,viewing,query-builder,utils},assets}

# Create all CSS files (copy content from guide)
touch public/css/{base,ingestion,viewing,query-builder,modals}.css

# Create all JS files
touch public/js/state.js
touch public/js/auth.js
touch public/js/main.js
touch public/js/utils/{api,helpers}.js
touch public/js/ingestion/ingestion.js
touch public/js/viewing/{graph-viewer,cytoscape-manager,index-panel,modals}.js
touch public/js/query-builder/query-builder.js

# Copy index.html (provided)
# Copy updated server.js (provided)

# Start server
node server.js
```

## Testing Checklist

After extraction, test each feature:

- [ ] Authentication works
- [ ] PDF upload works
- [ ] Text upload works
- [ ] Graph loads and displays
- [ ] Node selection works (Shift+Click)
- [ ] Index panel toggles
- [ ] Search works
- [ ] Query builder works
- [ ] Modals display correctly
- [ ] Export functions work
- [ ] Review queue link works

## Common Issues & Fixes

**Issue**: Module not found errors
**Fix**: Check import paths are correct, use relative paths (../, ./)

**Issue**: "X is not defined"
**Fix**: Ensure proper imports at top of file, check state.js exports

**Issue**: Functions not accessible from onclick
**Fix**: Expose managers to window object in main.js

**Issue**: CSS not loading
**Fix**: Check paths in index.html match file structure (/static/css/...)

**Issue**: API calls failing
**Fix**: Ensure Node server is proxying correctly to Python backend