/**
 * Workspaces Landing Page
 * Handles workspace listing, creation, and navigation
 */

import { API } from '../utils/api.js';

class WorkspacesManager {
  constructor() {
    console.log('🚀 WorkspacesManager constructor called');
    this.workspaces = [];
    this.currentUser = null;
    this.selectedIcon = '📊';
    this.selectedColor = '#3B82F6';
    this.editingWorkspaceId = null;
    this.workspaceRefreshTimeout = null;
    this.handleWorkspaceRefresh = this.handleWorkspaceRefresh.bind(this);
    window.addEventListener('workspaceNeedsRefresh', this.handleWorkspaceRefresh);

    this.init();
  }

  getMemberDisplayName(member) {
    const first = (member.user_first_name || '').trim();
    const last = (member.user_last_name || '').trim();
    const name = `${first} ${last}`.trim();
    if (name) return name;
    const email = member.user_email || '';
    const local = email.split('@')[0] || '';
    if (!local) return email;
    const parts = local.split(/[._-]+/).filter(Boolean);
    if (parts.length === 0) return local;
    return parts.map(p => p.charAt(0).toUpperCase() + p.slice(1)).join(' ');
  }

  createGlobalViewCard() {
    const totals = this.computeTotals();
    const workspaceCount = this.globalStats?.workspace_count || this.workspaces.length;
    const card = document.createElement('div');
    card.className = 'workspace-card';
    card.innerHTML = `
      <div class="workspace-header">
        <div class="workspace-icon">🌐</div>
        <div class="workspace-title">Global View</div>
      </div>
      <div class="workspace-description">View all content across all workspaces</div>
      <div class="workspace-stats">
        <div class="stat"><span>📄</span><span id="global-card-docs-count">${totals.documents} docs</span></div>
        <div class="stat"><span>🔗</span><span id="global-card-entities-count">${totals.entities} entities</span></div>
      </div>
      <div class="workspace-footer">
        <div class="last-activity">Across <span id="global-card-workspaces-count">${workspaceCount}</span> workspaces</div>
        <div class="workspace-actions">
          <button class="action-button primary" id="open-global">Open</button>
        </div>
      </div>
    `;
    card.querySelector('#open-global').addEventListener('click', (e) => {
      e.stopPropagation();
      this.openGlobalView();
    });
    card.addEventListener('click', () => this.openGlobalView());
    return card;
  }

  async init() {
    console.log('🔧 Initializing WorkspacesManager');
    // Check authentication
    await this.checkAuth();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Load workspaces
    await this.loadWorkspaces();

    // If navigated with #settings=<workspaceId>, auto-open settings
    const hash = window.location.hash || '';
    if (hash.startsWith('#settings=')) {
      const wsId = decodeURIComponent(hash.split('=')[1] || '');
      if (wsId) {
        this.openWorkspaceSettings(wsId);
      }
    }
  }

  async checkAuth() {
    try {
      const response = await API.get('/api/me');
      this.currentUser = response.user;
      
      // Update UI with user info
      const userName = `${this.currentUser.first_name} ${this.currentUser.last_name}`.trim() || this.currentUser.email;
      document.getElementById('user-name').textContent = userName;
    } catch (error) {
      console.error('Not authenticated:', error);
      // Redirect to login
      window.location.href = '/login';
    }
  }

  setupEventListeners() {
    // User menu
    const userButton = document.getElementById('user-button');
    const userDropdown = document.getElementById('user-dropdown');
    if (userButton && userDropdown) {
      userButton.addEventListener('click', (e) => {
        e.stopPropagation();
        userDropdown.classList.toggle('show');
      });
      document.addEventListener('click', () => {
        userDropdown.classList.remove('show');
      });
    }

    // Logout
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
      logoutLink.addEventListener('click', async (e) => {
        e.preventDefault();
        await this.logout();
      });
    }

    // Retry button
    const retryBtn = document.getElementById('retry-button');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.loadWorkspaces();
      });
    }

    // Global view button (legacy, removed in rehaul) – guard if present
    const globalBtn = document.getElementById('global-view-button');
    if (globalBtn) {
      globalBtn.addEventListener('click', () => {
        this.openGlobalView();
      });
    }

    // Modal controls
    const modalClose = document.getElementById('modal-close');
    if (modalClose) modalClose.addEventListener('click', () => this.closeModal());

    const cancelBtn = document.getElementById('cancel-button');
    if (cancelBtn) cancelBtn.addEventListener('click', () => this.closeModal());

    // Settings modal controls
    const wsClose = document.getElementById('ws-settings-close');
    const wsCancel = document.getElementById('ws-settings-cancel');
    if (wsClose) wsClose.addEventListener('click', () => this.closeSettingsModal());
    if (wsCancel) wsCancel.addEventListener('click', () => this.closeSettingsModal());

    // Settings save
    const wsForm = document.getElementById('workspace-settings-form');
    if (wsForm) {
      wsForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.saveWorkspaceSettings();
      });
    }

    // Create workspace form
    document.getElementById('create-workspace-form').addEventListener('submit', (e) => {
      e.preventDefault();
      this.createWorkspace();
    });

    // Icon selector
    document.querySelectorAll('.icon-option').forEach(button => {
      button.addEventListener('click', () => {
        document.querySelectorAll('.icon-option').forEach(b => b.classList.remove('selected'));
        button.classList.add('selected');
        this.selectedIcon = button.dataset.icon;
        document.getElementById('workspace-icon').value = this.selectedIcon;
      });
    });

    // Color selector
    document.querySelectorAll('.color-option').forEach(button => {
      button.addEventListener('click', () => {
        document.querySelectorAll('.color-option').forEach(b => b.classList.remove('selected'));
        button.classList.add('selected');
        this.selectedColor = button.dataset.color;
        document.getElementById('workspace-color').value = this.selectedColor;
      });
    });

    // Set default selections
    document.querySelector('.icon-option[data-icon="📊"]').classList.add('selected');
    document.querySelector('.color-option[data-color="#3B82F6"]').classList.add('selected');
  }

  async loadWorkspaces() {
    const loadingState = document.getElementById('loading-state');
    const errorState = document.getElementById('error-state');
    const workspacesGrid = document.getElementById('workspaces-grid');

    // Show loading
    loadingState.style.display = 'block';
    errorState.style.display = 'none';
    workspacesGrid.innerHTML = '';

    try {
      // Fetch workspaces
      const response = await API.get('/api/workspaces');
      this.workspaces = response;

      // Hide loading
      loadingState.style.display = 'none';

      // Load global stats FIRST so initial render uses real totals
      await this.loadGlobalStats();

      // Render workspaces (Global card will use cached globalStats)
      this.renderWorkspaces();

    } catch (error) {
      console.error('Failed to load workspaces:', error);
      loadingState.style.display = 'none';
      errorState.style.display = 'block';
      document.getElementById('error-message').textContent = 
        error.message || 'Failed to load workspaces. Please try again.';
    }
  }

  handleWorkspaceRefresh(event) {
    const { workspaceId } = event?.detail || {};
    if (this.workspaceRefreshTimeout) {
      clearTimeout(this.workspaceRefreshTimeout);
    }
    this.workspaceRefreshTimeout = setTimeout(() => {
      // Optionally we could filter by workspaceId in the future
      this.loadWorkspaces();
    }, 300);
  }

  renderWorkspaces() {
    const grid = document.getElementById('workspaces-grid');
    grid.innerHTML = '';

    // Add create new workspace card
    const createCard = this.createNewWorkspaceCard();
    grid.appendChild(createCard);

    // Add Global View card (same size as other cards)
    const globalCard = this.createGlobalViewCard();
    grid.appendChild(globalCard);

    // Add workspace cards
    this.workspaces.forEach(workspace => {
      const card = this.createWorkspaceCard(workspace);
      grid.appendChild(card);
    });
  }

  createNewWorkspaceCard() {
    const card = document.createElement('div');
    card.className = 'create-workspace-card';
    card.innerHTML = `
      <div class="create-icon">➕</div>
      <h3>Create New Workspace</h3>
      <p>Organize your research into focused workspaces</p>
    `;

    card.addEventListener('click', () => {
      this.openCreateModal();
    });

    return card;
  }

  createWorkspaceCard(workspace) {
    const card = document.createElement('div');
    card.className = 'workspace-card';
    card.style.setProperty('--workspace-color', workspace.color);

    const privacy = (workspace.privacy || 'private').toLowerCase();
    const hasMultipleMembers = workspace.members && workspace.members.length > 1;
    const isShared = privacy !== 'private' || hasMultipleMembers;
    const stats = workspace.stats || {};
    const owner = (workspace.members || []).find(m => m.role === 'owner');
    const createdByMe = owner && owner.user_id === this.currentUser.user_id;
    const creatorName = owner ? this.getMemberDisplayName(owner) : null;

    card.innerHTML = `
      <div class="workspace-header">
        <div class="workspace-icon">${workspace.icon}</div>
        <div class="workspace-title">${this.escapeHtml(workspace.name)}</div>
        ${isShared ? '<span class="workspace-badge">Shared</span>' : ''}
      </div>
      
      ${workspace.description ? `
        <div class="workspace-description">${this.escapeHtml(workspace.description)}</div>
      ` : ''}
      
      <div class="workspace-stats">
        <div class="stat">
          <span>📄</span>
          <span>${stats.document_count || 0} docs</span>
        </div>
        <div class="stat">
          <span>🔗</span>
          <span>${stats.entity_count || 0} entities</span>
        </div>
      </div>
      
      <div class="workspace-footer">
        <div class="last-activity">${!createdByMe && creatorName ? `by ${this.escapeHtml(creatorName)} • ` : ''}${this.formatLastActivity(workspace.updated_at || workspace.created_at)}</div>
        <div class="workspace-actions">
          <button class="action-button settings-button" data-workspace-id="${workspace.workspace_id}">
            ⚙️
          </button>
          <button class="action-button primary open-button" data-workspace-id="${workspace.workspace_id}">
            Open
          </button>
        </div>
      </div>
    `;

    // Event listeners
    const openButton = card.querySelector('.open-button');
    openButton.addEventListener('click', (e) => {
      e.stopPropagation();
      this.openWorkspace(workspace.workspace_id);
    });

    const settingsButton = card.querySelector('.settings-button');
    settingsButton.addEventListener('click', (e) => {
      e.stopPropagation();
      this.openWorkspaceSettings(workspace.workspace_id);
    });

    // Click on card to show details
    card.addEventListener('click', () => {
      this.showWorkspaceDetails(workspace.workspace_id);
    });

    return card;
  }

  openCreateModal() {
    const modal = document.getElementById('create-workspace-modal');
    modal.classList.add('show');
    document.body.classList.add('modal-open');

    // Reset form
    document.getElementById('create-workspace-form').reset();
    this.selectedIcon = '📊';
    this.selectedColor = '#3B82F6';
    document.querySelectorAll('.icon-option').forEach(b => b.classList.remove('selected'));
    document.querySelectorAll('.color-option').forEach(b => b.classList.remove('selected'));
    document.querySelector('.icon-option[data-icon="📊"]').classList.add('selected');
    document.querySelector('.color-option[data-color="#3B82F6"]').classList.add('selected');
  }

  closeModal() {
    const modal = document.getElementById('create-workspace-modal');
    modal.classList.remove('show');
    document.body.classList.remove('modal-open');
  }

  async createWorkspace() {
    const submitButton = document.getElementById('submit-button');
    const originalText = submitButton.textContent;

    try {
      submitButton.disabled = true;
      submitButton.textContent = 'Creating...';

      const name = document.getElementById('workspace-name').value.trim();
      const description = document.getElementById('workspace-description').value.trim();
      const privacy = document.querySelector('input[name="privacy"]:checked').value;

      const payload = {
        name,
        description: description || null,
        icon: this.selectedIcon,
        color: this.selectedColor,
        privacy
      };

      const newWorkspace = await API.post('/api/workspaces', payload);

      // Close modal
      this.closeModal();

      // Reload workspaces
      await this.loadWorkspaces();

      // Show success message (optional)
      console.log('Workspace created:', newWorkspace);

    } catch (error) {
      console.error('Failed to create workspace:', error);
      alert('Failed to create workspace: ' + (error.message || 'Unknown error'));
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = originalText;
    }
  }

  openWorkspace(workspaceId) {
    // Store workspace ID in session storage
    sessionStorage.setItem('currentWorkspaceId', workspaceId);
    
    // Navigate to main app
    window.location.href = '/app';
  }

  openWorkspaceSettings(workspaceId) {
    this.editingWorkspaceId = workspaceId;
    this.loadWorkspaceAndOpenSettings(workspaceId);
  }

  async loadWorkspaceAndOpenSettings(workspaceId) {
    try {
      const ws = await API.get(`/api/workspaces/${encodeURIComponent(workspaceId)}`);
      // Populate fields
      document.getElementById('ws-settings-name').value = ws.name || '';
      document.getElementById('ws-settings-description').value = ws.description || '';

      // Render icon/color selectors with current selected
      this.renderSettingsIconColor(ws.icon, ws.color);

      // Set privacy
      const privacy = ws.privacy || 'private';
      const radios = document.querySelectorAll('input[name="ws-settings-privacy"]');
      radios.forEach(r => { r.checked = (r.value === privacy); });

      // Open modal
      const modal = document.getElementById('workspace-settings-modal');
      modal.classList.add('show');
      document.body.classList.add('modal-open');
    } catch (e) {
      console.error('Failed to load workspace for settings', e);
      alert('Failed to load workspace settings');
    }
  }

  renderSettingsIconColor(selectedIcon, selectedColor) {
    const icons = ['📊','🧬','🔬','🧪','💉','🌱','🔭','⚗️','🧫','📚'];
    const colors = ['#3B82F6','#10B981','#F59E0B','#EF4444','#8B5CF6','#EC4899'];
    const iconSel = document.getElementById('ws-settings-icon-selector');
    const colorSel = document.getElementById('ws-settings-color-selector');
    iconSel.innerHTML = icons.map(ic => `<button type="button" class="icon-option ${ic===selectedIcon?'selected':''}" data-icon="${ic}">${ic}</button>`).join('');
    colorSel.innerHTML = colors.map(c => `<button type="button" class="color-option ${c===selectedColor?'selected':''}" data-color="${c}" style="background:${c}"></button>`).join('');

    iconSel.querySelectorAll('.icon-option').forEach(btn => {
      btn.addEventListener('click', () => {
        iconSel.querySelectorAll('.icon-option').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
      });
    });
    colorSel.querySelectorAll('.color-option').forEach(btn => {
      btn.addEventListener('click', () => {
        colorSel.querySelectorAll('.color-option').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
      });
    });
  }

  async saveWorkspaceSettings() {
    if (!this.editingWorkspaceId) return;
    const name = document.getElementById('ws-settings-name').value.trim();
    const description = document.getElementById('ws-settings-description').value.trim();
    const iconBtn = document.querySelector('#ws-settings-icon-selector .icon-option.selected');
    const colorBtn = document.querySelector('#ws-settings-color-selector .color-option.selected');
    const privacy = document.querySelector('input[name="ws-settings-privacy"]:checked')?.value;

    const payload = {
      name: name || undefined,
      description: description || undefined,
      icon: iconBtn ? iconBtn.dataset.icon : undefined,
      color: colorBtn ? colorBtn.dataset.color : undefined,
      privacy: privacy || undefined
    };

    try {
      await API.put(`/api/workspaces/${encodeURIComponent(this.editingWorkspaceId)}`, payload);
      this.closeSettingsModal();
      await this.loadWorkspaces();
    } catch (e) {
      console.error('Failed to save settings', e);
      alert('Failed to save workspace settings');
    }
  }

  closeSettingsModal() {
    const modal = document.getElementById('workspace-settings-modal');
    modal.classList.remove('show');
    document.body.classList.remove('modal-open');
    this.editingWorkspaceId = null;
  }

  openGlobalView() {
    // Clear workspace selection
    sessionStorage.removeItem('currentWorkspaceId');
    
    // Navigate to main app in global view mode
    window.location.href = '/app?view=global';
  }

  async loadGlobalStats() {
    const statsEl = document.getElementById('global-stats');
    
    try {
      // Fetch actual global stats from backend
      const stats = await API.get('/api/workspaces/global/stats');
      if (statsEl) {
        statsEl.innerHTML = `${stats.document_count} documents • ${stats.entity_count} entities • ${stats.workspace_count} workspaces`;
      }
      
      // Store for Global View card
      this.globalStats = stats;

      // Update Global View card counts if present
      const docsCountEl = document.getElementById('global-card-docs-count');
      const entitiesCountEl = document.getElementById('global-card-entities-count');
      const workspacesCountEl = document.getElementById('global-card-workspaces-count');
      if (docsCountEl) docsCountEl.textContent = `${stats.document_count} docs`;
      if (entitiesCountEl) entitiesCountEl.textContent = `${stats.entity_count} entities`;
      if (workspacesCountEl) workspacesCountEl.textContent = `${stats.workspace_count}`;
    } catch (error) {
      console.error('Failed to load global stats:', error);
      // Fallback to computing from workspace stats
      const totals = this.computeTotals();
      if (statsEl) statsEl.innerHTML = `${totals.documents} documents • ${totals.entities} entities • ${this.workspaces.length} workspaces`;
    }
  }

  computeTotals() {
    // Use cached global stats if available
    if (this.globalStats) {
      return { 
        documents: this.globalStats.document_count, 
        entities: this.globalStats.entity_count 
      };
    }
    
    // Fallback: sum from workspace stats
    const totalDocs = this.workspaces.reduce((sum, w) => sum + (w.stats?.document_count || 0), 0);
    const totalEntities = this.workspaces.reduce((sum, w) => sum + (w.stats?.entity_count || 0), 0);
    return { documents: totalDocs, entities: totalEntities };
  }

  async logout() {
    try {
      await API.post('/api/auth/logout');
      window.location.href = '/api/auth/login';
    } catch (error) {
      console.error('Logout failed:', error);
      // Force redirect anyway
      window.location.href = '/api/auth/login';
    }
  }

  formatLastActivity(dateString) {
    if (!dateString) return 'Never';

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  async showWorkspaceDetails(workspaceId) {
    const modal = document.getElementById('workspace-detail-modal');
    if (!modal) return;

    // Show modal immediately
    modal.classList.add('show');
    document.body.classList.add('modal-open');

    // Set up event listeners if not already done
    if (!this.detailModalListenersSet) {
      this.setupDetailModalListeners();
      this.detailModalListenersSet = true;
    }

    // Store current workspace ID
    this.currentDetailWorkspaceId = workspaceId;

    try {
      // Load workspace details
      const workspace = await API.get(`/api/workspaces/${encodeURIComponent(workspaceId)}`);
      
      // Populate workspace info (both in overview and stats)
      document.getElementById('detail-icon').textContent = workspace.icon || '📊';
      document.getElementById('detail-name').textContent = workspace.name || 'Untitled';
      document.getElementById('detail-description').textContent = workspace.description || 'No description';
      document.getElementById('detail-privacy').textContent = workspace.privacy === 'private' ? 'Private' : 'Shared';
      document.getElementById('detail-created').textContent = this.formatLastActivity(workspace.created_at);
      
      const stats = workspace.stats || {};
      const memberCount = workspace.members?.length || stats.member_count || 0;
      document.getElementById('detail-members').textContent = memberCount;
      document.getElementById('detail-docs').textContent = stats.document_count || 0;
      document.getElementById('detail-entities').textContent = stats.entity_count || 0;
      document.getElementById('detail-rels').textContent = stats.relationship_count || 0;

      // Populate members list
      this.populateMembersList(workspace.members || []);

      // Populate activity (placeholder for now)
      this.populateActivity(workspace);

      // Load documents, entities, and relationships (for Content tab)
      await this.loadWorkspaceDocuments(workspaceId);
      await this.loadWorkspaceEntities(workspaceId);
      await this.loadWorkspaceRelationships(workspaceId);
    } catch (error) {
      console.error('Failed to load workspace details:', error);
      alert('Failed to load workspace details');
      this.closeDetailModal();
    }
  }

  populateMembersList(members) {
    const listEl = document.getElementById('detail-members-list');
    if (!listEl) return;

    if (members.length === 0) {
      listEl.innerHTML = '<div class="detail-empty"><p>No members</p></div>';
      return;
    }

    listEl.innerHTML = members.map(member => {
      const displayName = this.getMemberDisplayName(member);
      const roleColor = member.role === 'owner' ? '#667eea' : '#6b7280';
      return `
        <div class="detail-item">
          <div class="detail-item-header">
            <div class="detail-item-title">👤 ${this.escapeHtml(displayName)}</div>
            <span style="color: ${roleColor}; font-weight: 600; font-size: 0.75rem; text-transform: uppercase;">${this.escapeHtml(member.role || 'member')}</span>
          </div>
          ${member.user_email ? `<div class="detail-item-content">${this.escapeHtml(member.user_email)}</div>` : ''}
        </div>
      `;
    }).join('');
  }

  populateActivity(workspace) {
    const listEl = document.getElementById('detail-activity');
    if (!listEl) return;

    // For now, show basic activity info
    const activities = [];
    
    if (workspace.created_at) {
      activities.push({
        type: 'created',
        message: 'Workspace created',
        timestamp: workspace.created_at
      });
    }

    if (workspace.updated_at && workspace.updated_at !== workspace.created_at) {
      activities.push({
        type: 'updated',
        message: 'Workspace updated',
        timestamp: workspace.updated_at
      });
    }

    if (activities.length === 0) {
      listEl.innerHTML = '<div class="detail-empty"><p>No recent activity</p></div>';
      return;
    }

    listEl.innerHTML = activities.map(activity => `
      <div class="detail-item">
        <div class="detail-item-header">
          <div class="detail-item-title">${activity.message}</div>
          <div class="detail-item-meta">${this.formatLastActivity(activity.timestamp)}</div>
        </div>
      </div>
    `).join('');
  }

  setupDetailModalListeners() {
    const modal = document.getElementById('workspace-detail-modal');
    const closeBtn = document.getElementById('ws-detail-close');
    const closeBtnFooter = document.getElementById('ws-detail-close-btn');
    const openBtn = document.getElementById('ws-detail-open');

    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeDetailModal());
    }

    if (closeBtnFooter) {
      closeBtnFooter.addEventListener('click', () => this.closeDetailModal());
    }

    if (openBtn) {
      openBtn.addEventListener('click', () => {
        if (this.currentDetailWorkspaceId) {
          this.openWorkspace(this.currentDetailWorkspaceId);
        }
      });
    }

    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.closeDetailModal();
      });
    }

    // Main tab switching (Overview / Content)
    const mainTabs = document.querySelectorAll('.detail-main-tab');
    mainTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;
        
        // Update active tab
        mainTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update active pane
        document.querySelectorAll('.detail-main-pane').forEach(pane => {
          pane.classList.remove('active');
        });
        document.getElementById(`${targetTab}-pane`).classList.add('active');
      });
    });

    // Sub-tab switching (Documents / Entities / Relationships)
    const subTabs = document.querySelectorAll('.detail-sub-tab');
    subTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const targetTab = tab.dataset.tab;
        
        // Update active tab
        subTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update active pane
        document.querySelectorAll('.detail-sub-pane').forEach(pane => {
          pane.classList.remove('active');
        });
        document.getElementById(`${targetTab}-pane`).classList.add('active');
      });
    });
  }

  closeDetailModal() {
    const modal = document.getElementById('workspace-detail-modal');
    if (modal) {
      modal.classList.remove('show');
      document.body.classList.remove('modal-open');
    }
    this.currentDetailWorkspaceId = null;
  }

  async loadWorkspaceDocuments(workspaceId) {
    const listEl = document.getElementById('documents-list');
    if (!listEl) return;

    listEl.innerHTML = '<div class="detail-loading">Loading documents...</div>';

    try {
      const response = await API.get(`/api/workspaces/${encodeURIComponent(workspaceId)}/documents`);
      const documents = response.documents || response || [];

      if (documents.length === 0) {
        listEl.innerHTML = '<div class="detail-empty"><div class="detail-empty-icon">📄</div><p>No documents yet</p></div>';
        return;
      }

      listEl.innerHTML = documents.map(doc => `
        <div class="detail-item">
          <div class="detail-item-header">
            <div class="detail-item-title">${this.escapeHtml(doc.title || doc.name || 'Untitled')}</div>
            <div class="detail-item-meta">${this.formatLastActivity(doc.created_at)}</div>
          </div>
          ${doc.summary ? `<div class="detail-item-content">${this.escapeHtml(doc.summary)}</div>` : ''}
        </div>
      `).join('');
    } catch (error) {
      console.error('Failed to load documents:', error);
      listEl.innerHTML = '<div class="detail-empty"><p>Failed to load documents</p></div>';
    }
  }

  async loadWorkspaceEntities(workspaceId) {
    const listEl = document.getElementById('entities-list');
    if (!listEl) return;

    listEl.innerHTML = '<div class="detail-loading">Loading entities...</div>';

    try {
      const response = await API.get(`/api/workspaces/${encodeURIComponent(workspaceId)}/entities`);
      const entities = response.entities || response || [];

      if (entities.length === 0) {
        listEl.innerHTML = '<div class="detail-empty"><div class="detail-empty-icon">🔗</div><p>No entities yet</p></div>';
        return;
      }

      listEl.innerHTML = entities.map(entity => `
        <div class="detail-item">
          <div class="detail-item-header">
            <div class="detail-item-title">${this.escapeHtml(entity.name || entity.label || 'Unnamed')}</div>
            ${entity.type ? `<span class="entity-type-badge">${this.escapeHtml(entity.type)}</span>` : ''}
          </div>
          ${entity.description ? `<div class="detail-item-content">${this.escapeHtml(entity.description)}</div>` : ''}
        </div>
      `).join('');
    } catch (error) {
      console.error('Failed to load entities:', error);
      listEl.innerHTML = '<div class="detail-empty"><p>Failed to load entities</p></div>';
    }
  }

  async loadWorkspaceRelationships(workspaceId) {
    const listEl = document.getElementById('relationships-list');
    if (!listEl) return;

    listEl.innerHTML = '<div class="detail-loading">Loading relationships...</div>';

    try {
      const response = await API.get(`/api/workspaces/${encodeURIComponent(workspaceId)}/relationships`);
      const relationships = response.relationships || response || [];

      if (relationships.length === 0) {
        listEl.innerHTML = '<div class="detail-empty"><div class="detail-empty-icon">↔️</div><p>No relationships yet</p></div>';
        return;
      }

      listEl.innerHTML = relationships.map(rel => `
        <div class="relationship-wrapper">
          <div class="relationship-type">${this.escapeHtml(rel.type || rel.relationship_type || 'RELATED')}</div>
          <div class="relationship-node">${this.escapeHtml(rel.source_name || rel.from || 'Node')}</div>
          <div class="relationship-arrow">→</div>
          <div class="relationship-node">${this.escapeHtml(rel.target_name || rel.to || 'Node')}</div>
        </div>
      `).join('');
    } catch (error) {
      console.error('Failed to load relationships:', error);
      listEl.innerHTML = '<div class="detail-empty"><p>Failed to load relationships</p></div>';
    }
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new WorkspacesManager();
  });
} else {
  new WorkspacesManager();
}
