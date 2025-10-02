"""Main unified UI with Ingestion and Viewing tabs, integrated with authentication."""
from fastapi import APIRouter, Response


router = APIRouter()


HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Knowledge Synthesis Platform</title>
    <style>
      * { box-sizing: border-box; }
      html, body { height: 100%; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }
      
      #header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 16px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
      }
      
      #header h1 { margin: 0; font-size: 24px; font-weight: 600; }
      
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
      
      #user-info button:hover { background: rgba(255,255,255,0.3); }
      
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
      .tab.active { color: #667eea; border-bottom-color: #667eea; background: white; }
      
      .tab-content {
        display: none;
        height: calc(100vh - 120px);
        overflow: hidden;
      }
      
      .tab-content.active { display: block; }
      
      /* Ingestion Tab Styles */
      #ingestion-panel {
        max-width: 1400px;
        margin: 20px auto;
        padding: 0 24px;
        height: calc(100vh - 180px);
        display: flex;
        align-items: center;
      }
      
      .card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 28px 32px;
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
      
      .custom-file-upload:active {
        transform: translateY(0);
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
      
      .param-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
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
      
      button.primary:hover { background: #5568d3; }
      button.primary:disabled {
        background: #9ca3af;
        cursor: not-allowed;
      }
      
      #ingest-status {
        margin-top: 16px;
        padding: 12px;
        border-radius: 6px;
        display: none;
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
      
      /* Progress Bar Styles */
      .progress-container {
        margin-top: 12px;
        padding: 12px;
        background: #f3f4f6;
        border-radius: 6px;
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
      
      .current-file-status {
        margin-top: 8px;
        font-size: 12px;
        color: #6b7280;
      }
      
      .file-list-status {
        margin-top: 12px;
        max-height: 150px;
        overflow-y: auto;
      }
      
      .file-status-item {
        padding: 6px 8px;
        margin: 4px 0;
        border-radius: 4px;
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .file-status-item.pending {
        background: #f3f4f6;
        color: #6b7280;
      }
      
      .file-status-item.processing {
        background: #dbeafe;
        color: #1e40af;
      }
      
      .file-status-item.success {
        background: #d1fae5;
        color: #065f46;
      }
      
      .file-status-item.error {
        background: #fee2e2;
        color: #991b1b;
      }
      
      /* Viewing Tab Styles */
      #viewing-panel {
        display: grid;
        grid-template-columns: 1fr 0fr;
        height: 100%;
        overflow: hidden;
        transition: grid-template-columns 0.3s ease;
      }
      
      #viewing-panel.details-visible {
        grid-template-columns: 3fr 1fr !important;
      }
      
      #cy-container {
        position: relative;
        background: #fafafa;
        overflow: hidden;
        height: 100%;
        min-width: 0;
      }
      
      #cy { 
        width: 100%; 
        height: 100%;
      }
      
      #view-controls {
        position: absolute;
        top: 12px;
        left: 12px;
        background: white;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        max-width: 320px;
        z-index: 10;
      }
      
      #view-controls select {
        width: 100%;
        margin-bottom: 8px;
      }
      
      #view-controls button {
        width: 100%;
        margin-bottom: 8px;
      }
      
      #view-controls input[type="text"] {
        width: 100%;
        margin-bottom: 8px;
      }
      
      #view-controls label {
        display: block;
        font-size: 13px;
        margin-bottom: 8px;
        cursor: pointer;
      }
      
      #view-controls label input[type="checkbox"] {
        margin-right: 6px;
        width: auto;
      }
      
      #details-panel {
        border-left: 1px solid #e5e7eb;
        background: white;
        overflow-y: auto;
        overflow-x: hidden;
        height: 100%;
        min-width: 0;
        opacity: 0;
        transition: opacity 0.3s ease;
      }
      
      #details-panel.visible {
        opacity: 1;
        padding: 20px;
      }
      
      #details-panel h3 {
        margin: 0 0 16px 0;
        color: #111827;
      }
      
      .detail-section {
        margin-bottom: 20px;
        padding-bottom: 20px;
        border-bottom: 1px solid #e5e7eb;
      }
      
      .detail-section:last-child { border-bottom: none; }
      
      .detail-label {
        font-weight: 600;
        color: #6b7280;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
      }
      
      .detail-value {
        color: #111827;
        font-size: 14px;
      }
      
      .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
      }
      
      .status-unverified { background: #fef3c7; color: #92400e; }
      .status-verified { background: #d1fae5; color: #065f46; }
      .status-incorrect { background: #fee2e2; color: #991b1b; }
    </style>
    <script src="https://unpkg.com/cytoscape@3.29.2/dist/cytoscape.min.js"></script>
    <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
  </head>
  <body>
    <div id="header">
      <h1>🧠 Knowledge Synthesis Platform</h1>
      <div id="user-info">
        <span>👤 <span id="username">Guest</span></span>
        <button onclick="logout()">Logout</button>
      </div>
    </div>
    
    <div id="tabs">
      <div class="tab active" onclick="switchTab('ingestion')">📤 Ingestion</div>
      <div class="tab" onclick="switchTab('viewing')">🔍 Viewing</div>
      <div class="tab" onclick="window.open('/review-ui', '_blank')">✅ Review Queue</div>
    </div>
    
    <!-- Ingestion Tab -->
    <div id="ingestion-tab" class="tab-content active">
      <div id="ingestion-panel">
        <div class="card">
          <h2>📤 Document Ingestion & Knowledge Extraction</h2>
          
          <div class="ingestion-grid">
            <!-- Left Column: Document Upload -->
            <div>
              <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #374151; font-weight: 600;">Document Source</h3>
              
              <div class="form-group">
                <label>Upload PDF File(s)</label>
                <label for="pdf-file" class="custom-file-upload">
                  📄 Choose PDF Files
                </label>
                <input type="file" id="pdf-file" accept=".pdf" multiple onchange="displayFileName()" />
                <div id="file-name" class="file-name-display">No files selected</div>
              </div>
              
              <div class="form-group">
                <label>Or Paste Text Directly</label>
                <textarea id="text-input" placeholder="Paste your document text here..." style="min-height: 90px;"></textarea>
                <div class="help-text">You can paste raw text instead of uploading a file</div>
              </div>
              
              <div class="form-group">
                <label>Document Title (Optional)</label>
                <input type="text" id="doc-title" placeholder="e.g., Research Paper on BRAF Mutations" />
                <div class="help-text">Friendly name for this document</div>
              </div>
            </div>
            
            <!-- Right Column: Extraction Parameters -->
            <div>
              <h3 style="margin: 0 0 16px 0; font-size: 16px; color: #374151; font-weight: 600;">Extraction Settings</h3>
              
              <div class="form-group">
                <label>Max Concepts</label>
                <input type="number" id="max-concepts" value="100" min="10" max="500" />
                <div class="help-text">Maximum number of entities to extract (10-500)</div>
              </div>
              
              <div class="form-group">
                <label>Max Relationships</label>
                <input type="number" id="max-relationships" value="50" min="10" max="200" />
                <div class="help-text">Maximum number of triplets to extract (10-200)</div>
              </div>
              
              <div class="form-group">
                <label>Extraction Model</label>
                <select id="model-select">
                  <option value="gpt-4o-mini">GPT-4o Mini (Fast, Cost-effective)</option>
                  <option value="gpt-4o">GPT-4o (Higher Quality)</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo</option>
                </select>
                <div class="help-text">AI model for knowledge extraction</div>
              </div>
              
              <button class="primary" id="ingest-btn" onclick="ingestDocument()" style="margin-top: 16px; width: 100%; padding: 14px; font-size: 16px;">
                🚀 Extract Knowledge
              </button>
              
              <div id="ingest-status"></div>
              
              <!-- Progress Bar -->
              <div id="progress-container" class="progress-container">
                <div class="progress-header">
                  <span id="progress-text">Processing...</span>
                  <span id="progress-count">0 / 0</span>
                </div>
                <div class="progress-bar-bg">
                  <div id="progress-bar-fill" class="progress-bar-fill" style="width: 0%;">
                    <span id="progress-percentage">0%</span>
                  </div>
                </div>
                <div id="current-file-status" class="current-file-status"></div>
                <div id="file-list-status" class="file-list-status"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Viewing Tab -->
    <div id="viewing-tab" class="tab-content">
      <div id="viewing-panel">
        <div id="cy-container">
          <div id="cy"></div>
          <div id="view-controls">
            <button class="primary" onclick="loadAllData()">🔄 Reload All</button>
            <select id="doc-select" multiple size="5"></select>
            <button class="primary" onclick="loadSelectedDocuments()">Filter to Selected</button>
            <input type="text" id="search-input" placeholder="Search concept..." />
            <button class="primary" onclick="searchConcept()">Search</button>
            <label>
              <input type="checkbox" id="verified-only" />
              Show verified only
            </label>
            <label>
              <input type="checkbox" id="show-negative" checked />
              Show negative relationships
            </label>
          </div>
        </div>
        
        <div id="details-panel">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <h3 style="margin: 0;">Details</h3>
            <button onclick="hideDetails()" style="background: transparent; border: none; font-size: 20px; cursor: pointer; color: #6b7280;">×</button>
          </div>
          <div id="details-content"></div>
        </div>
      </div>
    </div>
    
    <script>
      // Global state
      let currentUser = null;
      let cy = null;
      
      // Initialize
      async function init() {
        await checkAuth();
        await loadDocuments();
        // Don't initialize cytoscape or load data until viewing tab is opened
        // This prevents the horizontal line issue
      }
      
      async function checkAuth() {
        try {
          const res = await fetch('/api/auth/me', {
            credentials: 'include'  // Include cookies
          });
          if (res.ok) {
            const data = await res.json();
            currentUser = data.user;
            document.getElementById('username').textContent = currentUser.username || currentUser.user_id;
          } else {
            // Not authenticated, redirect to login
            window.location.href = '/login';
          }
        } catch (e) {
          console.error('Auth check failed:', e);
          window.location.href = '/login';
        }
      }
      
      let graphInitialized = false;
      
      function switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        
        event.target.classList.add('active');
        document.getElementById(tabName + '-tab').classList.add('active');
        
        if (tabName === 'viewing') {
          if (!graphInitialized) {
            // First time opening viewing tab - initialize everything
            console.log('Initializing graph for first time...');
            // Use requestAnimationFrame to ensure DOM is ready
            requestAnimationFrame(() => {
              initCytoscape();
              setTimeout(async () => {
                if (cy) {
                  cy.resize();
                }
                await loadAllData();
                graphInitialized = true;
              }, 150);
            });
          } else if (cy) {
            // Already initialized, just resize and fit
            requestAnimationFrame(() => {
              cy.resize();
              cy.fit(undefined, 20);
            });
            setTimeout(() => {
              cy.resize();
            }, 100);
          }
        }
      }
      
      async function logout() {
        try {
          await fetch('/api/auth/logout', { 
            method: 'POST',
            credentials: 'include'
          });
        } catch (e) {
          console.error('Logout failed:', e);
        }
        window.location.href = '/login';
      }
      
      // Ingestion functions
      function displayFileName() {
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
      
      async function ingestDocument() {
        const pdfFiles = document.getElementById('pdf-file').files;
        const text = document.getElementById('text-input').value.trim();
        const title = document.getElementById('doc-title').value.trim();
        const maxConcepts = parseInt(document.getElementById('max-concepts').value);
        const maxRelationships = parseInt(document.getElementById('max-relationships').value);
        const model = document.getElementById('model-select').value;
        
        if (pdfFiles.length === 0 && !text) {
          showStatus('error', 'Please upload PDF file(s) or paste text');
          return;
        }
        
        const btn = document.getElementById('ingest-btn');
        btn.disabled = true;
        
        // Handle text input (single document)
        if (!pdfFiles.length && text) {
          showStatus('processing', 'Processing text... This may take 30-60 seconds.');
          try {
            const response = await fetch('/ingest/text', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                text,
                document_title: title || 'Text Upload',
                document_id: `user-${currentUser.user_id}-${Date.now()}`,
                user_id: currentUser.user_id,
                user_first_name: currentUser.first_name || '',
                user_last_name: currentUser.last_name || '',
                max_concepts: maxConcepts,
                max_relationships: maxRelationships
              })
            });
            
            if (!response.ok) {
              const error = await response.json();
              throw new Error(error.detail || 'Ingestion failed');
            }
            
            const result = await response.json();
            showStatus('success', `✓ Success! Extracted ${result.triplets} relationships.`);
            
            // Clear form
            document.getElementById('text-input').value = '';
            document.getElementById('doc-title').value = '';
            await loadDocuments();
          } catch (e) {
            showStatus('error', '✗ Error: ' + e.message);
          } finally {
            btn.disabled = false;
          }
          return;
        }
        
        // Handle PDF file(s) - multiple files with progress bar
        if (pdfFiles.length > 0) {
          showProgress(true);
          hideStatus();
          
          const files = Array.from(pdfFiles);
          const totalFiles = files.length;
          const results = {
            successful: 0,
            failed: 0,
            totalTriplets: 0
          };
          
          // Initialize file list status
          const fileListEl = document.getElementById('file-list-status');
          fileListEl.innerHTML = files.map((file, index) => 
            `<div id="file-status-${index}" class="file-status-item pending">
              <span>⏳</span>
              <span>${file.name}</span>
            </div>`
          ).join('');
          
          try {
            for (let i = 0; i < files.length; i++) {
              const file = files[i];
              const fileStatusEl = document.getElementById(`file-status-${i}`);
              
              // Update progress
              updateProgress(i + 1, totalFiles, `Processing: ${file.name}`);
              fileStatusEl.className = 'file-status-item processing';
              fileStatusEl.innerHTML = `<span>⏳</span><span>${file.name}</span>`;
              
              try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('user_id', currentUser.user_id);
                formData.append('user_first_name', currentUser.first_name || '');
                formData.append('user_last_name', currentUser.last_name || '');
                formData.append('max_concepts', maxConcepts);
                formData.append('max_relationships', maxRelationships);
                if (title && totalFiles === 1) formData.append('title', title);
                
                const response = await fetch('/ingest/pdf', {
                  method: 'POST',
                  body: formData
                });
                
                if (!response.ok) {
                  const error = await response.json();
                  throw new Error(error.detail || 'Ingestion failed');
                }
                
                const result = await response.json();
                results.successful++;
                results.totalTriplets += result.triplets;
                
                fileStatusEl.className = 'file-status-item success';
                fileStatusEl.innerHTML = `<span>✓</span><span>${file.name} (${result.triplets} relationships)</span>`;
              } catch (e) {
                results.failed++;
                fileStatusEl.className = 'file-status-item error';
                fileStatusEl.innerHTML = `<span>✗</span><span>${file.name} - ${e.message}</span>`;
              }
            }
            
            // Show final summary
            updateProgress(totalFiles, totalFiles, 'Complete!');
            setTimeout(() => {
              showProgress(false);
              if (results.failed === 0) {
                showStatus('success', 
                  `✓ All ${results.successful} file(s) processed successfully! Total: ${results.totalTriplets} relationships extracted.`
                );
              } else {
                showStatus('error', 
                  `⚠ Processed ${results.successful} file(s) successfully, ${results.failed} failed. Total: ${results.totalTriplets} relationships extracted.`
                );
              }
            }, 1500);
            
            // Clear form
            document.getElementById('pdf-file').value = '';
            document.getElementById('doc-title').value = '';
            displayFileName();
            await loadDocuments();
            
          } catch (e) {
            showProgress(false);
            showStatus('error', '✗ Error: ' + e.message);
          } finally {
            btn.disabled = false;
          }
        }
      }
      
      function showProgress(show) {
        const progressContainer = document.getElementById('progress-container');
        if (show) {
          progressContainer.classList.add('active');
        } else {
          progressContainer.classList.remove('active');
        }
      }
      
      function updateProgress(current, total, statusText) {
        const percentage = Math.round((current / total) * 100);
        document.getElementById('progress-bar-fill').style.width = percentage + '%';
        document.getElementById('progress-percentage').textContent = percentage + '%';
        document.getElementById('progress-count').textContent = `${current} / ${total}`;
        document.getElementById('progress-text').textContent = statusText;
        document.getElementById('current-file-status').textContent = statusText;
      }
      
      function hideStatus() {
        const statusEl = document.getElementById('ingest-status');
        statusEl.className = '';
        statusEl.textContent = '';
      }
      
      function showStatus(type, message) {
        const statusEl = document.getElementById('ingest-status');
        statusEl.className = type;
        statusEl.textContent = message;
      }
      
      // Viewing functions
      function initCytoscape() {
        cytoscape.use(cytoscapeDagre);
        
        cy = cytoscape({
          container: document.getElementById('cy'),
          elements: [],
          wheelSensitivity: 0.2,
          minZoom: 0.1,
          maxZoom: 3,
          style: [
            {
              selector: 'node',
              style: {
                'label': 'data(label)',
                'font-size': '12px',
                'text-wrap': 'wrap',
                'text-max-width': 150,
                'text-halign': 'center',
                'text-valign': 'center',
                'background-color': '#667eea',
                'color': '#ffffff',
                'text-outline-color': '#667eea',
                'text-outline-width': 2,
                'width': 50,
                'height': 50,
                'border-width': 2,
                'border-color': '#5568d3'
              }
            },
            {
              selector: 'edge',
              style: {
                'curve-style': 'bezier',
                'target-arrow-shape': 'triangle',
                'width': 2.5,
                'line-color': '#94a3b8',
                'target-arrow-color': '#94a3b8',
                'label': 'data(relation)',
                'font-size': '11px',
                'color': '#374151',
                'text-background-color': '#ffffff',
                'text-background-opacity': 0.8,
                'text-background-padding': 3,
                'edge-text-rotation': 'autorotate'
              }
            },
            {
              selector: 'edge[status = "verified"]',
              style: {
                'line-color': '#059669',
                'target-arrow-color': '#059669',
                'width': 3.5
              }
            },
            {
              selector: 'edge[status = "incorrect"]',
              style: {
                'line-color': '#dc2626',
                'target-arrow-color': '#dc2626',
                'line-style': 'dashed',
                'width': 2
              }
            },
            {
              selector: 'edge[polarity = "negative"]',
              style: {
                'line-style': 'dotted'
              }
            },
            {
              selector: 'node:selected',
              style: {
                'background-color': '#1d4ed8',
                'border-color': '#1e40af',
                'border-width': 3
              }
            },
            {
              selector: 'edge:selected',
              style: {
                'line-color': '#1d4ed8',
                'target-arrow-color': '#1d4ed8',
                'width': 4
              }
            }
          ]
        });
        
        cy.on('tap', 'node', showNodeDetails);
        cy.on('tap', 'edge', showEdgeDetails);
        
        // Hide details on background click
        cy.on('tap', (evt) => {
          if (evt.target === cy) {
            hideDetails();
          }
        });
      }
      
      async function loadDocuments() {
        try {
          const res = await fetch('/query/documents');
          const docs = await res.json();
          
          const select = document.getElementById('doc-select');
          select.innerHTML = docs.map(d => 
            `<option value="${d.id}">${d.title || d.id}</option>`
          ).join('');
          
          return docs;
        } catch (e) {
          console.error('Failed to load documents:', e);
          return [];
        }
      }
      
      async function loadAllData() {
        try {
          const res = await fetch('/query/all');
          const data = await res.json();
          
          const nodeCount = (data.nodes || []).length;
          const edgeCount = (data.relationships || []).length;
          
          if (nodeCount === 0 && edgeCount === 0) {
            // No data yet - show helpful message
            alert('No data in the knowledge graph yet. Upload a document in the Ingestion tab to get started!');
            return;
          }
          
          // Ensure cytoscape is ready and properly sized
          if (cy) {
            cy.resize();
          }
          
          renderGraph(data);
        } catch (e) {
          console.error('Failed to load all data:', e);
          alert('Failed to load graph data: ' + e.message);
        }
      }
      
      async function loadSelectedDocuments() {
        const select = document.getElementById('doc-select');
        const selected = Array.from(select.selectedOptions).map(o => o.value);
        
        if (selected.length === 0) {
          alert('Please select at least one document');
          return;
        }
        
        const verifiedOnly = document.getElementById('verified-only').checked;
        
        try {
          const url = `/query/graph_by_docs?doc_ids=${selected.join(',')}&verified_only=${verifiedOnly}`;
          const res = await fetch(url);
          const data = await res.json();
          
          renderGraph(data);
        } catch (e) {
          alert('Failed to load graph: ' + e.message);
        }
      }
      
      async function searchConcept() {
        const query = document.getElementById('search-input').value.trim();
        if (!query) {
          alert('Please enter a search term');
          return;
        }
        
        const verifiedOnly = document.getElementById('verified-only').checked;
        
        try {
          const url = `/query/search/concept?name=${encodeURIComponent(query)}&verified_only=${verifiedOnly}`;
          const res = await fetch(url);
          const data = await res.json();
          
          renderGraph(data);
        } catch (e) {
          alert('Search failed: ' + e.message);
        }
      }
      
      function renderGraph(data) {
        const elements = [];
        
        (data.nodes || []).forEach(n => {
          elements.push({
            data: {
              id: n.id,
              label: n.label || n.id,
              type: n.type,
              sources: n.sources
            }
          });
        });
        
        (data.relationships || []).forEach(r => {
          elements.push({
            data: {
              id: r.id,
              source: r.source,
              target: r.target,
              relation: r.relation,
              status: r.status || 'unverified',
              polarity: r.polarity || 'positive',
              confidence: r.confidence,
              sources: r.sources,
              reviewed_by_first_name: r.reviewed_by_first_name,
              reviewed_by_last_name: r.reviewed_by_last_name,
              reviewed_at: r.reviewed_at
            }
          });
        });
        
        cy.elements().remove();
        
        if (elements.length === 0) {
          // Show empty state
          document.getElementById('details-content').innerHTML = `
            <p style="color: #6b7280; text-align: center; padding: 20px;">
              No data to display.<br><br>
              Select documents and click "Load Graph" or use the search function.
            </p>
          `;
          return;
        }
        
        cy.add(elements);
        
        // Use a better layout based on graph size
        const nodeCount = (data.nodes || []).length;
        let layoutConfig;
        
        if (nodeCount > 50) {
          // For large graphs, use force-directed layout
          layoutConfig = {
            name: 'cose',
            idealEdgeLength: 100,
            nodeOverlap: 20,
            refresh: 20,
            fit: true,
            padding: 30,
            randomize: false,
            componentSpacing: 100,
            nodeRepulsion: 400000,
            edgeElasticity: 100,
            nestingFactor: 5,
            gravity: 80,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0
          };
        } else {
          // For smaller graphs, use hierarchical layout
          layoutConfig = {
            name: 'dagre',
            rankSep: 100,
            nodeSep: 80,
            edgeSep: 20,
            rankDir: 'TB',  // Top to bottom
            ranker: 'network-simplex',
            fit: true,
            padding: 30
          };
        }
        
        // Ensure container is properly sized before layout
        cy.resize();
        
        const layout = cy.layout(layoutConfig);
        layout.run();
        
        // Fit after layout completes
        layout.on('layoutstop', () => {
          setTimeout(() => {
            cy.fit(undefined, 30);
          }, 50);
        });
      }
      
      function showNodeDetails(evt) {
        const node = evt.target;
        const data = node.data();
        
        console.log('Node clicked:', data);
        console.log('Node sources:', data.sources);
        
        // Show details panel
        showDetailsPanel();
        
        const detailsContent = document.getElementById('details-content');
        if (!detailsContent) {
          console.error('details-content element not found!');
          return;
        }
        
        const sources = data.sources || [];
        console.log('Sources array:', sources, 'Length:', sources.length);
        let sourcesHtml = '';
        if (sources.length === 0 || !sources || (sources.length === 1 && !sources[0].id)) {
          sourcesHtml = '<div class="detail-value" style="color: #ef4444;">No sources recorded</div>';
        } else {
          sourcesHtml = `
            <div class="detail-value" style="font-weight: 600;">${sources.length} document(s)</div>
            <div style="margin-top: 8px; font-size: 12px; color: #6b7280;">
              ${sources.map(s => {
                const title = (typeof s === 'object' && s.title) ? s.title : s;
                const firstName = (typeof s === 'object' && s.created_by_first_name) ? s.created_by_first_name : '';
                const lastName = (typeof s === 'object' && s.created_by_last_name) ? s.created_by_last_name : '';
                const userName = firstName && lastName ? ` — by ${firstName} ${lastName}` : '';
                return `<div style="padding: 4px 0; border-bottom: 1px solid #e5e7eb;">📄 ${title}<span style="color: #6b7280; font-size: 12px;">${userName}</span></div>`;
              }).join('')}
            </div>
          `;
        }
        
        detailsContent.innerHTML = `
          <div class="detail-section">
            <div class="detail-label">Node</div>
            <div class="detail-value" style="font-weight: 600; font-size: 16px;">${data.label}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">Type</div>
            <div class="detail-value">${data.type || 'N/A'}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">ID</div>
            <div class="detail-value" style="font-family: monospace; font-size: 12px;">${data.id}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">Sources</div>
            ${sourcesHtml}
          </div>
        `;
      }
      
      function showEdgeDetails(evt) {
        const edge = evt.target;
        const data = edge.data();
        
        console.log('Edge clicked:', data);
        
        // Show details panel
        showDetailsPanel();
        
        const statusClass = `status-${data.status || 'unverified'}`;
        const sources = data.sources || [];
        
        let sourcesHtml = '';
        if (sources.length === 0) {
          sourcesHtml = '<div class="detail-value" style="color: #ef4444;">No sources recorded</div>';
        } else {
          sourcesHtml = `
            <div class="detail-value" style="font-weight: 600;">${sources.length} document(s)</div>
            <div style="margin-top: 8px; font-size: 12px; color: #6b7280;">
              ${sources.map(s => {
                // s is now an object with {id, title, created_by_first_name, created_by_last_name}
                const title = (typeof s === 'object' && s.title) ? s.title : s;
                const firstName = (typeof s === 'object' && s.created_by_first_name) ? s.created_by_first_name : '';
                const lastName = (typeof s === 'object' && s.created_by_last_name) ? s.created_by_last_name : '';
                const userName = firstName && lastName ? ` — by ${firstName} ${lastName}` : '';
                return `<div style="padding: 4px 0; border-bottom: 1px solid #e5e7eb;">📄 ${title}<span style="color: #6b7280; font-size: 12px;">${userName}</span></div>`;
              }).join('')}
            </div>
          `;
        }
        
        // Build reviewer info if available
        let reviewerHtml = '';
        if (data.status === 'verified' || data.status === 'incorrect') {
          const reviewerFirstName = data.reviewed_by_first_name || '';
          const reviewerLastName = data.reviewed_by_last_name || '';
          const reviewerName = reviewerFirstName && reviewerLastName ? 
            `${reviewerFirstName} ${reviewerLastName}` : 
            (reviewerFirstName || reviewerLastName || 'Unknown');
          
          const reviewDate = data.reviewed_at ? new Date(data.reviewed_at).toLocaleString() : 'N/A';
          const actionText = data.status === 'verified' ? 'Verified' : 'Flagged';
          
          reviewerHtml = `
            <div class="detail-section">
              <div class="detail-label">${actionText} By</div>
              <div class="detail-value">
                <div style="font-weight: 600;">${reviewerName}</div>
                <div style="font-size: 12px; color: #6b7280; margin-top: 4px;">${reviewDate}</div>
              </div>
            </div>
          `;
        }
        
        document.getElementById('details-content').innerHTML = `
          <div class="detail-section">
            <div class="detail-label">Relationship</div>
            <div class="detail-value" style="font-weight: 600; font-size: 16px; color: #667eea;">${data.relation}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">From → To</div>
            <div class="detail-value" style="line-height: 1.6;">
              <div><strong>From:</strong> ${data.source}</div>
              <div><strong>To:</strong> ${data.target}</div>
            </div>
          </div>
          <div class="detail-section">
            <div class="detail-label">Status</div>
            <div class="detail-value">
              <span class="status-badge ${statusClass}">${data.status || 'unverified'}</span>
            </div>
          </div>
          ${reviewerHtml}
          <div class="detail-section">
            <div class="detail-label">Sources</div>
            ${sourcesHtml}
          </div>
        `;
      }
      
      function showDetailsPanel() {
        const panel = document.getElementById('details-panel');
        const viewingPanel = document.getElementById('viewing-panel');
        
        if (!panel || !viewingPanel) return;
        
        panel.classList.add('visible');
        viewingPanel.classList.add('details-visible');
        
        // Resize cytoscape multiple times to ensure it adapts
        if (cy) {
          requestAnimationFrame(() => {
            cy.resize();
            cy.fit(null, 50);
          });
          setTimeout(() => {
            cy.resize();
            cy.fit(null, 50);
          }, 100);
          setTimeout(() => {
            cy.resize();
          }, 350);
        }
      }
      
      function hideDetails() {
        const panel = document.getElementById('details-panel');
        const viewingPanel = document.getElementById('viewing-panel');
        
        if (!panel || !viewingPanel) return;
        
        panel.classList.remove('visible');
        viewingPanel.classList.remove('details-visible');
        
        if (cy) {
          cy.elements().unselect();
          
          // Resize cytoscape multiple times to ensure it adapts
          requestAnimationFrame(() => {
            cy.resize();
            cy.fit(null, 50);
          });
          setTimeout(() => {
            cy.resize();
            cy.fit(null, 50);
          }, 100);
          setTimeout(() => {
            cy.resize();
          }, 350);
        }
      }
      
      // Initialize on load
      init();
    </script>
  </body>
</html>
""".strip()


@router.get("")
def serve_main_ui():
    """Serve the main unified UI with Ingestion and Viewing tabs."""
    return Response(content=HTML, media_type="text/html")

