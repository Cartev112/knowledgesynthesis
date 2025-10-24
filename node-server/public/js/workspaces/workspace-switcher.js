/**
 * Workspace Switcher Component
 * Dropdown component for switching between workspaces in the main app
 */

import { API } from '../utils/api.js';

class WorkspaceSwitcher {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.workspaces = [];
    this.currentWorkspace = null;
    this.currentUser = null;
    
    this.init();
  }

  async init() {
    if (!this.container) {
      console.warn('Workspace switcher container not found');
      return;
    }

    // Get current user
    await this.loadCurrentUser();
    
    // Load current workspace from session
    const workspaceId = sessionStorage.getItem('currentWorkspaceId');
    
    // Load workspaces
    await this.loadWorkspaces();
    
    // Set current workspace
    if (workspaceId) {
      this.currentWorkspace = this.workspaces.find(w => w.workspace_id === workspaceId);
    }
    
    // Render the switcher
    this.render();
    
    // Set up event listeners
    this.setupEventListeners();
    
    // Emit workspace change event
    this.emitWorkspaceChange();
  }

  async loadCurrentUser() {
    try {
      const response = await API.get('/api/me');
      this.currentUser = response.user;
    } catch (error) {
      console.error('Failed to load current user:', error);
    }
  }

  async loadWorkspaces() {
    try {
      this.workspaces = await API.get('/api/workspaces');
    } catch (error) {
      console.error('Failed to load workspaces:', error);
      this.workspaces = [];
    }
  }

  render() {
    const currentName = this.currentWorkspace 
      ? this.currentWorkspace.name 
      : 'Global View';
    
    const currentIcon = this.currentWorkspace 
      ? this.currentWorkspace.icon 
      : '🌐';

    const workspacesList = this.workspaces
      .filter(w => !this.currentWorkspace || w.workspace_id !== this.currentWorkspace.workspace_id)
      .map(workspace => `
        <div class="ws-item" data-workspace-id="${workspace.workspace_id}">
          <span class="ws-item-icon">${workspace.icon}</span>
          <span class="ws-item-name">${this.escapeHtml(workspace.name)}</span>
          ${workspace.members && workspace.members.length > 1 ? '<span class="ws-shared">Shared</span>' : ''}
        </div>
      `).join('');

    this.container.innerHTML = `
      <div class="workspace-switcher ws-center">
        <button class="ws-current-button" id="ws-current-button" aria-haspopup="dialog" aria-controls="ws-modal">
          <span class="ws-icon">${currentIcon}</span>
          <span class="ws-name">${this.escapeHtml(currentName)}</span>
        </button>
      </div>

      <div class="ws-modal" id="ws-modal" role="dialog" aria-modal="true" aria-labelledby="ws-modal-title">
        <div class="ws-modal-dialog">
          <div class="ws-modal-header">
            <h3 id="ws-modal-title">Switch Workspace</h3>
            <button class="ws-modal-close" id="ws-modal-close" aria-label="Close">×</button>
          </div>
          <div class="ws-modal-body">
            <div class="ws-section">
              <div class="ws-label">Current</div>
              <div class="ws-item ${!this.currentWorkspace ? 'active' : ''}" data-workspace-id="">
                <span class="ws-item-icon">🌐</span>
                <span class="ws-item-name">Global View</span>
                ${!this.currentWorkspace ? '<span class="ws-check">✓</span>' : ''}
              </div>
              ${this.currentWorkspace ? `
              <div class="ws-item active" data-workspace-id="${this.currentWorkspace.workspace_id}">
                <span class="ws-item-icon">${this.currentWorkspace.icon}</span>
                <span class="ws-item-name">${this.escapeHtml(this.currentWorkspace.name)}</span>
                <span class="ws-check">✓</span>
              </div>` : ''}
            </div>

            ${this.workspaces.length > 0 ? `
            <div class="ws-divider"></div>
            <div class="ws-section">
              <div class="ws-label">Your Workspaces</div>
              <div class="ws-list">${workspacesList || '<div class="ws-empty">No other workspaces</div>'}</div>
            </div>` : ''}
          </div>
          <div class="ws-modal-footer">
            <button class="ws-action" id="create-workspace-action">➕ Create New</button>
            <button class="ws-action" id="manage-workspaces-action">🏠 Manage</button>
            ${this.currentWorkspace ? '<button class="ws-action" id="workspace-settings-action">⚙️ Settings</button>' : ''}
          </div>
        </div>
      </div>
    `;
  }

  setupEventListeners() {
    const trigger = document.getElementById('ws-current-button');
    const modal = document.getElementById('ws-modal');
    const dialog = modal?.querySelector('.ws-modal-dialog');
    const closeBtn = document.getElementById('ws-modal-close');

    if (trigger) {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        this.openModal();
      });
    }

    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeModal());
    }

    // Close when clicking outside dialog
    if (modal && dialog) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.closeModal();
      });
      dialog.addEventListener('click', (e) => e.stopPropagation());
    }

    // Workspace selection
    modal?.querySelectorAll('.ws-item[data-workspace-id]')?.forEach(item => {
      item.addEventListener('click', () => {
        const workspaceId = item.dataset.workspaceId;
        this.switchWorkspace(workspaceId);
        this.closeModal();
      });
    });

    // Create workspace action
    const createAction = document.getElementById('create-workspace-action');
    if (createAction) {
      createAction.addEventListener('click', () => {
        window.location.href = '/workspaces.html';
        this.closeModal();
      });
    }

    // Manage workspaces action
    const manageAction = document.getElementById('manage-workspaces-action');
    if (manageAction) {
      manageAction.addEventListener('click', () => {
        window.location.href = '/workspaces.html';
        this.closeModal();
      });
    }

    // Workspace settings action
    const settingsAction = document.getElementById('workspace-settings-action');
    if (settingsAction) {
      settingsAction.addEventListener('click', () => {
        this.openWorkspaceSettings();
        this.closeModal();
      });
    }
  }

  openModal() {
    const modal = document.getElementById('ws-modal');
    if (modal) modal.classList.add('show');
  }

  closeModal() {
    const modal = document.getElementById('ws-modal');
    if (modal) modal.classList.remove('show');
  }

  switchWorkspace(workspaceId) {
    if (workspaceId) {
      // Switch to specific workspace
      sessionStorage.setItem('currentWorkspaceId', workspaceId);
      this.currentWorkspace = this.workspaces.find(w => w.workspace_id === workspaceId);
    } else {
      // Switch to global view
      sessionStorage.removeItem('currentWorkspaceId');
      this.currentWorkspace = null;
    }

    // Re-render switcher
    this.render();
    this.setupEventListeners();

    // Emit workspace change event
    this.emitWorkspaceChange();

    // Reload the page to apply workspace filter
    window.location.reload();
  }

  emitWorkspaceChange() {
    // Dispatch custom event that other components can listen to
    const event = new CustomEvent('workspaceChanged', {
      detail: {
        workspace: this.currentWorkspace,
        workspaceId: this.currentWorkspace?.workspace_id || null,
        isGlobalView: !this.currentWorkspace
      }
    });
    window.dispatchEvent(event);
  }

  openWorkspaceSettings() {
    // TODO: Implement workspace settings modal
    alert('Workspace settings coming soon!');
  }

  getCurrentWorkspace() {
    return this.currentWorkspace;
  }

  getCurrentWorkspaceId() {
    return this.currentWorkspace?.workspace_id || null;
  }

  isGlobalView() {
    return !this.currentWorkspace;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

export { WorkspaceSwitcher };
export default WorkspaceSwitcher;
