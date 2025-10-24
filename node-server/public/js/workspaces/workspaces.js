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
    
    this.init();
  }

  createGlobalViewCard() {
    const totals = this.computeTotals();
    const card = document.createElement('div');
    card.className = 'workspace-card';
    card.innerHTML = `
      <div class="workspace-header">
        <div class="workspace-icon">🌐</div>
        <div class="workspace-title">Global View</div>
      </div>
      <div class="workspace-description">View all content across all workspaces</div>
      <div class="workspace-stats">
        <div class="stat"><span>📄</span><span>${totals.documents} docs</span></div>
        <div class="stat"><span>🔗</span><span>${totals.entities} entities</span></div>
      </div>
      <div class="workspace-footer">
        <div class="last-activity">Across ${this.workspaces.length} workspaces</div>
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
    
    userButton.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('show');
    });

    document.addEventListener('click', () => {
      userDropdown.classList.remove('show');
    });

    // Logout
    document.getElementById('logout-link').addEventListener('click', async (e) => {
      e.preventDefault();
      await this.logout();
    });

    // Retry button
    document.getElementById('retry-button').addEventListener('click', () => {
      this.loadWorkspaces();
    });

    // Global view button
    document.getElementById('global-view-button').addEventListener('click', () => {
      this.openGlobalView();
    });

    // Modal controls
    document.getElementById('modal-close').addEventListener('click', () => {
      this.closeModal();
    });

    document.getElementById('cancel-button').addEventListener('click', () => {
      this.closeModal();
    });

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

      // Render workspaces
      this.renderWorkspaces();

      // Load global stats
      this.loadGlobalStats();

    } catch (error) {
      console.error('Failed to load workspaces:', error);
      loadingState.style.display = 'none';
      errorState.style.display = 'block';
      document.getElementById('error-message').textContent = 
        error.message || 'Failed to load workspaces. Please try again.';
    }
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

    const isShared = workspace.members && workspace.members.length > 1;
    const stats = workspace.stats || {};
    const owner = (workspace.members || []).find(m => m.role === 'owner');
    const createdByMe = owner && owner.user_id === this.currentUser.user_id;
    const creatorName = owner ? ((owner.user_first_name || '') + ' ' + (owner.user_last_name || '')).trim() || owner.user_email : null;

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

    // Click on card to open
    card.addEventListener('click', () => {
      this.openWorkspace(workspace.workspace_id);
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
      const totals = this.computeTotals();
      if (statsEl) statsEl.innerHTML = `${totals.documents} documents • ${totals.entities} entities • ${this.workspaces.length} workspaces`;
    } catch (error) {
      console.error('Failed to load global stats:', error);
      statsEl.textContent = 'Stats unavailable';
    }
  }

  computeTotals() {
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
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new WorkspacesManager();
  });
} else {
  new WorkspacesManager();
}
