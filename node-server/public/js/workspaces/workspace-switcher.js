/**
 * Workspace Switcher Component
 * Dropdown component for switching between workspaces in the main app
 */

import API from '../utils/api.js';

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
      const response = await API.get('/api/auth/me');
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

    this.container.innerHTML = `
      <div class="workspace-switcher">
        <button class="workspace-switcher-button" id="workspace-switcher-button">
          <span class="workspace-icon">${currentIcon}</span>
          <span class="workspace-name">${this.escapeHtml(currentName)}</span>
          <span class="dropdown-arrow">▼</span>
        </button>
        
        <div class="workspace-dropdown" id="workspace-dropdown">
          <div class="dropdown-section">
            <div class="dropdown-label">Current Workspace</div>
            <div class="dropdown-item current ${!this.currentWorkspace ? 'active' : ''}" data-workspace-id="">
              <span class="item-icon">🌐</span>
              <span class="item-name">Global View</span>
              ${!this.currentWorkspace ? '<span class="check-icon">✓</span>' : ''}
            </div>
            ${this.currentWorkspace ? `
              <div class="dropdown-item current active" data-workspace-id="${this.currentWorkspace.workspace_id}">
                <span class="item-icon">${this.currentWorkspace.icon}</span>
                <span class="item-name">${this.escapeHtml(this.currentWorkspace.name)}</span>
                <span class="check-icon">✓</span>
              </div>
            ` : ''}
          </div>

          ${this.workspaces.length > 0 ? `
            <div class="dropdown-divider"></div>
            <div class="dropdown-section">
              <div class="dropdown-label">Your Workspaces</div>
              ${this.workspaces
                .filter(w => !this.currentWorkspace || w.workspace_id !== this.currentWorkspace.workspace_id)
                .map(workspace => `
                  <div class="dropdown-item" data-workspace-id="${workspace.workspace_id}">
                    <span class="item-icon">${workspace.icon}</span>
                    <span class="item-name">${this.escapeHtml(workspace.name)}</span>
                    ${workspace.members && workspace.members.length > 1 ? '<span class="shared-badge">Shared</span>' : ''}
                  </div>
                `).join('')}
            </div>
          ` : ''}

          <div class="dropdown-divider"></div>
          <div class="dropdown-section">
            <div class="dropdown-item action" id="create-workspace-action">
              <span class="item-icon">➕</span>
              <span class="item-name">Create New Workspace</span>
            </div>
            <div class="dropdown-item action" id="manage-workspaces-action">
              <span class="item-icon">🏠</span>
              <span class="item-name">Manage Workspaces</span>
            </div>
          </div>

          ${this.currentWorkspace ? `
            <div class="dropdown-divider"></div>
            <div class="dropdown-section">
              <div class="dropdown-item action" id="workspace-settings-action">
                <span class="item-icon">⚙️</span>
                <span class="item-name">Workspace Settings</span>
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  setupEventListeners() {
    const button = document.getElementById('workspace-switcher-button');
    const dropdown = document.getElementById('workspace-dropdown');

    // Toggle dropdown
    button.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('show');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', () => {
      dropdown.classList.remove('show');
    });

    // Prevent dropdown from closing when clicking inside
    dropdown.addEventListener('click', (e) => {
      e.stopPropagation();
    });

    // Workspace selection
    dropdown.querySelectorAll('.dropdown-item[data-workspace-id]').forEach(item => {
      item.addEventListener('click', () => {
        const workspaceId = item.dataset.workspaceId;
        this.switchWorkspace(workspaceId);
        dropdown.classList.remove('show');
      });
    });

    // Create workspace action
    const createAction = document.getElementById('create-workspace-action');
    if (createAction) {
      createAction.addEventListener('click', () => {
        window.location.href = '/workspaces.html';
        dropdown.classList.remove('show');
      });
    }

    // Manage workspaces action
    const manageAction = document.getElementById('manage-workspaces-action');
    if (manageAction) {
      manageAction.addEventListener('click', () => {
        window.location.href = '/workspaces.html';
        dropdown.classList.remove('show');
      });
    }

    // Workspace settings action
    const settingsAction = document.getElementById('workspace-settings-action');
    if (settingsAction) {
      settingsAction.addEventListener('click', () => {
        this.openWorkspaceSettings();
        dropdown.classList.remove('show');
      });
    }
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

export default WorkspaceSwitcher;
