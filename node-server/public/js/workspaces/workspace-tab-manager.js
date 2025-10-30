/**
 * Workspace Tab Manager
 * Handles workspace management within the main application tab
 */

import { API } from '../utils/api.js';

class WorkspaceTabManager {
  constructor() {
    this.workspaces = [];
    this.currentWorkspaceId = null;
    this.selectedIcon = '📊';
    this.selectedColor = '#3B82F6';
    this.globalStats = null;
    this.availableDocuments = [];
    this.selectedDocuments = new Set();
  }

  async init() {
    console.log('🚀 Initializing WorkspaceTabManager');
    await this.loadWorkspaces();
    this.setupEventListeners();
  }

  setupEventListeners() {
    // Retry button
    const retryBtn = document.getElementById('ws-retry-button');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => this.loadWorkspaces());
    }

    // Detail modal tabs
    document.querySelectorAll('.detail-main-tab').forEach(tab => {
      tab.addEventListener('click', (e) => this.switchDetailTab(e.target.dataset.tab));
    });

    // Detail modal sub-tabs
    document.querySelectorAll('.detail-sub-tab').forEach(tab => {
      tab.addEventListener('click', (e) => this.switchDetailSubTab(e.target.dataset.tab));
    });

    // Close buttons
    const closeButtons = ['ws-detail-close', 'ws-detail-close-btn'];
    closeButtons.forEach(id => {
      const btn = document.getElementById(id);
      if (btn) {
        btn.addEventListener('click', () => this.closeDetailModal());
      }
    });

    // Open workspace button
    const openBtn = document.getElementById('ws-detail-open');
    if (openBtn) {
      openBtn.addEventListener('click', () => this.openWorkspace());
    }

    // Manage tab buttons
    const showAddDocsBtn = document.getElementById('show-add-docs-btn');
    if (showAddDocsBtn) {
      showAddDocsBtn.addEventListener('click', () => this.showAvailableDocuments());
    }

    const saveViewConfigBtn = document.getElementById('save-view-config-btn');
    if (saveViewConfigBtn) {
      saveViewConfigBtn.addEventListener('click', () => this.saveViewConfiguration());
    }
  }

  async loadWorkspaces() {
    const loadingState = document.getElementById('ws-loading-state');
    const errorState = document.getElementById('ws-error-state');
    const grid = document.getElementById('workspaces-grid');

    try {
      if (loadingState) loadingState.style.display = 'block';
      if (errorState) errorState.style.display = 'none';
      if (grid) grid.innerHTML = '';

      // Load workspaces
      const response = await API.get('/api/workspaces');
      this.workspaces = response || [];

      // Load global stats
      try {
        const statsResponse = await API.get('/api/workspaces/global/stats');
        this.globalStats = statsResponse;
      } catch (err) {
        console.warn('Failed to load global stats:', err);
      }

      if (loadingState) loadingState.style.display = 'none';
      this.renderWorkspaces();
    } catch (error) {
      console.error('Failed to load workspaces:', error);
      if (loadingState) loadingState.style.display = 'none';
      if (errorState) {
        errorState.style.display = 'block';
        const errorMsg = document.getElementById('ws-error-message');
        if (errorMsg) {
          errorMsg.textContent = `Failed to load workspaces: ${error.message}`;
        }
      }
    }
  }

  renderWorkspaces() {
    const grid = document.getElementById('workspaces-grid');
    if (!grid) return;

    grid.innerHTML = '';

    // Add "Create New" card
    grid.appendChild(this.createNewWorkspaceCard());

    // Add "Global View" card
    grid.appendChild(this.createGlobalViewCard());

    // Add workspace cards
    this.workspaces.forEach(workspace => {
      grid.appendChild(this.createWorkspaceCard(workspace));
    });
  }

  createNewWorkspaceCard() {
    const card = document.createElement('div');
    card.className = 'workspace-card create-card';
    card.innerHTML = `
      <div class="workspace-header">
        <div class="workspace-icon">➕</div>
        <div class="workspace-title">Create New Workspace</div>
      </div>
      <div class="workspace-description">Start a new collaborative workspace</div>
    `;
    card.addEventListener('click', () => {
      // Trigger existing create workspace modal
      const modal = document.getElementById('app-create-workspace-modal');
      if (modal) modal.classList.add('visible');
    });
    return card;
  }

  createGlobalViewCard() {
    const stats = this.globalStats || {};
    const card = document.createElement('div');
    card.className = 'workspace-card';
    card.innerHTML = `
      <div class="workspace-header">
        <div class="workspace-icon">🌐</div>
        <div class="workspace-title">Global View</div>
      </div>
      <div class="workspace-description">View all public content</div>
      <div class="workspace-stats">
        <div class="stat"><span>📄</span><span>${stats.document_count || 0} docs</span></div>
        <div class="stat"><span>🔗</span><span>${stats.entity_count || 0} entities</span></div>
      </div>
      <div class="workspace-footer">
        <div class="last-activity">Across ${stats.workspace_count || 0} workspaces</div>
        <div class="workspace-actions">
          <button class="action-button primary">Open</button>
        </div>
      </div>
    `;
    card.addEventListener('click', () => this.openGlobalView());
    return card;
  }

  createWorkspaceCard(workspace) {
    const card = document.createElement('div');
    card.className = 'workspace-card';
    const stats = workspace.stats || {};
    const isOwner = workspace.members?.some(m => m.role === 'owner');

    card.innerHTML = `
      <div class="workspace-header">
        <div class="workspace-icon" style="background: ${workspace.color || '#3B82F6'}">${workspace.icon || '📊'}</div>
        <div class="workspace-title">${workspace.name}</div>
      </div>
      <div class="workspace-description">${workspace.description || 'No description'}</div>
      <div class="workspace-stats">
        <div class="stat"><span>📄</span><span>${stats.document_count || 0} docs</span></div>
        <div class="stat"><span>🔗</span><span>${stats.entity_count || 0} entities</span></div>
        <div class="stat"><span>↔️</span><span>${stats.relationship_count || 0} rels</span></div>
      </div>
      <div class="workspace-footer">
        <div class="last-activity">${stats.member_count || 0} members</div>
        <div class="workspace-actions">
          <button class="action-button secondary" data-action="details">Details</button>
          <button class="action-button primary" data-action="open">Open</button>
        </div>
      </div>
    `;

    // Event listeners
    card.querySelector('[data-action="details"]').addEventListener('click', (e) => {
      e.stopPropagation();
      this.showWorkspaceDetails(workspace.workspace_id);
    });

    card.querySelector('[data-action="open"]').addEventListener('click', (e) => {
      e.stopPropagation();
      this.openWorkspaceById(workspace.workspace_id);
    });

    return card;
  }

  async showWorkspaceDetails(workspaceId) {
    this.currentWorkspaceId = workspaceId;
    const modal = document.getElementById('workspace-detail-modal');
    if (!modal) return;

    modal.classList.add('visible');

    // Load workspace details
    try {
      const workspace = await API.get(`/api/workspaces/${workspaceId}`);
      this.populateWorkspaceDetails(workspace);
      
      // Load content for active tab
      this.switchDetailTab('overview');
    } catch (error) {
      console.error('Failed to load workspace details:', error);
      alert('Failed to load workspace details');
      this.closeDetailModal();
    }
  }

  populateWorkspaceDetails(workspace) {
    // Header info
    document.getElementById('detail-icon').textContent = workspace.icon || '📊';
    document.getElementById('detail-icon').style.background = workspace.color || '#3B82F6';
    document.getElementById('detail-name').textContent = workspace.name;
    document.getElementById('detail-description').textContent = workspace.description || 'No description';
    document.getElementById('detail-privacy').textContent = workspace.privacy || 'private';
    
    const createdDate = new Date(workspace.created_at);
    document.getElementById('detail-created').textContent = `Created ${createdDate.toLocaleDateString()}`;

    // Stats
    const stats = workspace.stats || {};
    document.getElementById('detail-members').textContent = stats.member_count || 0;
    document.getElementById('detail-docs').textContent = stats.document_count || 0;
    document.getElementById('detail-entities').textContent = stats.entity_count || 0;
    document.getElementById('detail-rels').textContent = stats.relationship_count || 0;

    // Members list
    const membersList = document.getElementById('detail-members-list');
    if (membersList && workspace.members) {
      membersList.innerHTML = workspace.members.map(member => {
        const name = this.getMemberDisplayName(member);
        return `
          <div class="member-item">
            <span class="member-avatar">👤</span>
            <div class="member-info">
              <div class="member-name">${name}</div>
              <div class="member-role">${member.role}</div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Load view config if exists
    if (workspace.view_config) {
      const config = workspace.view_config;
      const showIsACheckbox = document.getElementById('show-is-a-rels');
      if (showIsACheckbox) {
        showIsACheckbox.checked = config.show_is_a_relationships !== false;
      }
      
      const minSigInput = document.getElementById('min-node-sig');
      if (minSigInput && config.min_node_significance) {
        minSigInput.value = config.min_node_significance;
      }
      
      const layoutSelect = document.getElementById('layout-algo');
      if (layoutSelect && config.layout_algorithm) {
        layoutSelect.value = config.layout_algorithm;
      }
    }
  }

  getMemberDisplayName(member) {
    const first = (member.user_first_name || '').trim();
    const last = (member.user_last_name || '').trim();
    const name = `${first} ${last}`.trim();
    if (name) return name;
    return member.user_email || 'Unknown';
  }

  switchDetailTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.detail-main-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update panes
    document.querySelectorAll('.detail-main-pane').forEach(pane => {
      pane.classList.toggle('active', pane.id === `${tabName}-pane`);
    });

    // Load content for the tab
    if (tabName === 'content') {
      this.loadWorkspaceContent('documents');
    } else if (tabName === 'manage') {
      // Reset manage tab state
      const docsList = document.getElementById('available-docs-list');
      if (docsList) docsList.style.display = 'none';
    }
  }

  switchDetailSubTab(tabName) {
    // Update sub-tab buttons
    document.querySelectorAll('.detail-sub-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Update sub-panes
    document.querySelectorAll('.detail-sub-pane').forEach(pane => {
      pane.classList.toggle('active', pane.id === `${tabName}-pane`);
    });

    // Load content
    this.loadWorkspaceContent(tabName);
  }

  async loadWorkspaceContent(contentType) {
    if (!this.currentWorkspaceId) return;

    const listId = `${contentType}-list`;
    const listEl = document.getElementById(listId);
    if (!listEl) return;

    listEl.innerHTML = '<div class="detail-loading">Loading...</div>';

    try {
      const response = await API.get(`/api/workspaces/${this.currentWorkspaceId}/${contentType}`);
      const items = response[contentType] || [];

      if (items.length === 0) {
        listEl.innerHTML = `<div style="text-align: center; color: #9ca3af; padding: 24px;">No ${contentType} found</div>`;
        return;
      }

      listEl.innerHTML = items.map(item => {
        if (contentType === 'documents') {
          return `
            <div class="detail-item">
              <div class="detail-item-icon">📄</div>
              <div class="detail-item-info">
                <div class="detail-item-title">${item.title || item.name}</div>
                <div class="detail-item-meta">${item.creator_email || 'Unknown'}</div>
              </div>
            </div>
          `;
        } else if (contentType === 'entities') {
          return `
            <div class="detail-item">
              <div class="detail-item-icon">🔗</div>
              <div class="detail-item-info">
                <div class="detail-item-title">${item.name || item.label}</div>
                <div class="detail-item-meta">${item.type || 'Entity'}</div>
              </div>
            </div>
          `;
        } else if (contentType === 'relationships') {
          return `
            <div class="detail-item">
              <div class="detail-item-icon">↔️</div>
              <div class="detail-item-info">
                <div class="detail-item-title">${item.source_name} → ${item.target_name}</div>
                <div class="detail-item-meta">${item.type}</div>
              </div>
            </div>
          `;
        }
      }).join('');
    } catch (error) {
      console.error(`Failed to load ${contentType}:`, error);
      listEl.innerHTML = `<div style="text-align: center; color: #ef4444; padding: 24px;">Failed to load ${contentType}</div>`;
    }
  }

  async showAvailableDocuments() {
    const docsList = document.getElementById('available-docs-list');
    const btn = document.getElementById('show-add-docs-btn');
    
    if (!docsList) return;

    if (docsList.style.display === 'none') {
      // Show and load
      docsList.style.display = 'block';
      btn.textContent = '🔼 Hide Documents';
      
      docsList.innerHTML = '<div class="detail-loading">Loading available documents...</div>';
      
      try {
        const response = await API.get(`/api/documents/available?workspace_id=${this.currentWorkspaceId}`);
        this.availableDocuments = response.documents || [];
        
        if (this.availableDocuments.length === 0) {
          docsList.innerHTML = '<div style="text-align: center; color: #9ca3af; padding: 16px;">No documents available to add</div>';
          return;
        }

        docsList.innerHTML = this.availableDocuments.map(doc => `
          <div class="available-doc-item" style="padding: 12px; border-bottom: 1px solid #e5e7eb; display: flex; align-items: center; gap: 12px;">
            <input type="checkbox" class="doc-checkbox" data-doc-id="${doc.document_id}" style="width: 18px; height: 18px;">
            <div style="flex: 1;">
              <div style="font-weight: 600; margin-bottom: 4px;">${doc.title || doc.name}</div>
              <div style="font-size: 12px; color: #6b7280;">${doc.creator_email || 'Unknown'} • ${doc.workspaces?.length || 0} workspaces</div>
            </div>
          </div>
        `).join('');

        // Add select all button
        const selectAllBtn = document.createElement('button');
        selectAllBtn.className = 'btn-secondary';
        selectAllBtn.textContent = 'Select All';
        selectAllBtn.style.marginTop = '12px';
        selectAllBtn.addEventListener('click', () => {
          const checkboxes = docsList.querySelectorAll('.doc-checkbox');
          const allChecked = Array.from(checkboxes).every(cb => cb.checked);
          checkboxes.forEach(cb => cb.checked = !allChecked);
          selectAllBtn.textContent = allChecked ? 'Select All' : 'Deselect All';
        });

        const addBtn = document.createElement('button');
        addBtn.className = 'btn-primary';
        addBtn.textContent = '➕ Add Selected Documents';
        addBtn.style.marginTop = '12px';
        addBtn.style.marginLeft = '8px';
        addBtn.addEventListener('click', () => this.addSelectedDocuments());

        const btnContainer = document.createElement('div');
        btnContainer.appendChild(selectAllBtn);
        btnContainer.appendChild(addBtn);
        docsList.appendChild(btnContainer);

      } catch (error) {
        console.error('Failed to load available documents:', error);
        docsList.innerHTML = '<div style="text-align: center; color: #ef4444; padding: 16px;">Failed to load documents</div>';
      }
    } else {
      // Hide
      docsList.style.display = 'none';
      btn.textContent = '📄 Browse Available Documents';
    }
  }

  async addSelectedDocuments() {
    const checkboxes = document.querySelectorAll('.doc-checkbox:checked');
    const documentIds = Array.from(checkboxes).map(cb => cb.dataset.docId);

    if (documentIds.length === 0) {
      alert('Please select at least one document');
      return;
    }

    try {
      await API.post(`/api/workspaces/${this.currentWorkspaceId}/documents/add`, {
        document_ids: documentIds
      });

      alert(`Successfully added ${documentIds.length} document(s) to workspace`);
      
      // Refresh content tab
      this.loadWorkspaceContent('documents');
      
      // Hide available docs list
      document.getElementById('available-docs-list').style.display = 'none';
      document.getElementById('show-add-docs-btn').textContent = '📄 Browse Available Documents';
      
      // Reload workspaces to update stats
      await this.loadWorkspaces();
    } catch (error) {
      console.error('Failed to add documents:', error);
      alert('Failed to add documents: ' + error.message);
    }
  }

  async saveViewConfiguration() {
    const showIsA = document.getElementById('show-is-a-rels')?.checked;
    const minSig = document.getElementById('min-node-sig')?.value;
    const layout = document.getElementById('layout-algo')?.value;

    const viewConfig = {
      show_is_a_relationships: showIsA !== false,
      min_node_significance: minSig ? parseInt(minSig) : null,
      layout_algorithm: layout || 'cose',
      node_color_scheme: 'by-type',
      node_size_scheme: 'by-significance',
      label_display_mode: 'hover'
    };

    try {
      await API.put(`/api/workspaces/${this.currentWorkspaceId}`, {
        view_config: viewConfig
      });

      alert('View configuration saved successfully');
    } catch (error) {
      console.error('Failed to save view configuration:', error);
      alert('Failed to save configuration: ' + error.message);
    }
  }

  closeDetailModal() {
    const modal = document.getElementById('workspace-detail-modal');
    if (modal) modal.classList.remove('visible');
    this.currentWorkspaceId = null;
  }

  openWorkspace() {
    if (this.currentWorkspaceId) {
      this.openWorkspaceById(this.currentWorkspaceId);
    }
  }

  openWorkspaceById(workspaceId) {
    // Switch to viewing tab and set workspace
    if (window.workspaceSwitcher) {
      window.workspaceSwitcher.switchWorkspace(workspaceId);
    }
    if (window.appManager) {
      window.appManager.switchTab('viewing');
    }
    this.closeDetailModal();
  }

  openGlobalView() {
    // Switch to viewing tab with global view
    if (window.workspaceSwitcher) {
      window.workspaceSwitcher.switchToGlobal();
    }
    if (window.appManager) {
      window.appManager.switchTab('viewing');
    }
  }
}

// Export and initialize
export { WorkspaceTabManager };

// Auto-initialize when imported
if (!window.workspaceTabManager) {
  window.workspaceTabManager = new WorkspaceTabManager();
}
