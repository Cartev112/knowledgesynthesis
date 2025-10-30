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
              <div class="ws-label">Workspaces</div>
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

        
        this.openCreateWorkspaceModal();
      });
    }

    // Manage workspaces action
    const manageAction = document.getElementById('manage-workspaces-action');
    if (manageAction) {
      manageAction.addEventListener('click', () => {
        if (window.appManager) {
          window.appManager.switchTab('workspaces');
        }
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
    if (modal) {
      modal.classList.add('show');
      document.body.classList.add('modal-open');
    }
  }

  closeModal() {
    const modal = document.getElementById('ws-modal');
    if (modal) {
      modal.classList.remove('show');
      document.body.classList.remove('modal-open');
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

  async openWorkspaceSettings() {
    if (!this.currentWorkspace || !this.currentWorkspace.workspace_id) return;
    
    try {
      // Load workspace details
      const ws = await API.get(`/api/workspaces/${encodeURIComponent(this.currentWorkspace.workspace_id)}`);
      
      // Populate modal fields
      document.getElementById('app-ws-name').value = ws.name || '';
      document.getElementById('app-ws-description').value = ws.description || '';
      
      // Render icon/color selectors
      this.renderAppSettingsIconColor(ws.icon, ws.color);
      
      // Show modal
      const modal = document.getElementById('app-workspace-settings-modal');
      if (modal) {
        modal.classList.add('show');
        document.body.classList.add('modal-open');
      }
      
      // Set up modal event listeners if not already set
      if (!this.appSettingsListenersSet) {
        this.setupAppSettingsListeners();
        this.appSettingsListenersSet = true;
      }
    } catch (e) {
      console.error('Failed to load workspace settings:', e);
      alert('Failed to load workspace settings');
    }
  }
  
  renderAppSettingsIconColor(selectedIcon, selectedColor) {
    const icons = ['📊','🧬','🔬','🧪','💉','🌱','🔭','⚗️','🧫','📚'];
    const colors = ['#3B82F6','#10B981','#F59E0B','#EF4444','#8B5CF6','#EC4899'];
    const iconSel = document.getElementById('app-ws-icon-selector');
    const colorSel = document.getElementById('app-ws-color-selector');
    
    if (iconSel) {
      iconSel.innerHTML = icons.map(ic => 
        `<button type="button" class="icon-option ${ic===selectedIcon?'selected':''}" data-icon="${ic}">${ic}</button>`
      ).join('');
      
      iconSel.querySelectorAll('.icon-option').forEach(btn => {
        btn.addEventListener('click', () => {
          iconSel.querySelectorAll('.icon-option').forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
        });
      });
    }
    
    if (colorSel) {
      colorSel.innerHTML = colors.map(c => 
        `<button type="button" class="color-option ${c===selectedColor?'selected':''}" data-color="${c}" style="background:${c}"></button>`
      ).join('');
      
      colorSel.querySelectorAll('.color-option').forEach(btn => {
        btn.addEventListener('click', () => {
          colorSel.querySelectorAll('.color-option').forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
        });
      });
    }
  }
  
  setupAppSettingsListeners() {
    const modal = document.getElementById('app-workspace-settings-modal');
    const closeBtn = document.getElementById('app-ws-settings-close');
    const cancelBtn = document.getElementById('app-ws-settings-cancel');
    const form = document.getElementById('app-workspace-settings-form');
    
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeAppSettingsModal());
    }
    
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => this.closeAppSettingsModal());
    }
    
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.closeAppSettingsModal();
      });
    }
    
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.saveAppWorkspaceSettings();
      });
    }
  }
  
  async saveAppWorkspaceSettings() {
    if (!this.currentWorkspace || !this.currentWorkspace.workspace_id) return;
    
    const name = document.getElementById('app-ws-name').value.trim();
    const description = document.getElementById('app-ws-description').value.trim();
    const iconBtn = document.querySelector('#app-ws-icon-selector .icon-option.selected');
    const colorBtn = document.querySelector('#app-ws-color-selector .color-option.selected');
    
    const payload = {
      name: name || undefined,
      description: description || undefined,
      icon: iconBtn ? iconBtn.dataset.icon : undefined,
      color: colorBtn ? colorBtn.dataset.color : undefined
    };
    
    try {
      await API.put(`/api/workspaces/${encodeURIComponent(this.currentWorkspace.workspace_id)}`, payload);
      this.closeAppSettingsModal();
      
      // Reload to reflect changes
      window.location.reload();
    } catch (e) {
      console.error('Failed to save workspace settings:', e);
      alert('Failed to save workspace settings');
    }
  }
  
  closeAppSettingsModal() {
    const modal = document.getElementById('app-workspace-settings-modal');
    if (modal) {
      modal.classList.remove('show');
      document.body.classList.remove('modal-open');
    }
  }
  
  openCreateWorkspaceModal() {
    // Reset form
    const form = document.getElementById('app-create-workspace-form');
    if (form) form.reset();
    
    // Render icon/color selectors with defaults
    this.renderCreateIconColor('📊', '#3B82F6');
    
    // Show modal
    const modal = document.getElementById('app-create-workspace-modal');
    if (modal) {
      modal.classList.add('show');
      document.body.classList.add('modal-open');
    }
    
    // Set up modal event listeners if not already set
    if (!this.createListenersSet) {
      this.setupCreateListeners();
      this.createListenersSet = true;
    }
  }
  
  renderCreateIconColor(selectedIcon, selectedColor) {
    const icons = ['📊','🧬','🔬','🧪','💉','🌱','🔭','⚗️','🧫','📚'];
    const colors = ['#3B82F6','#10B981','#F59E0B','#EF4444','#8B5CF6','#EC4899'];
    const iconSel = document.getElementById('app-create-icon-selector');
    const colorSel = document.getElementById('app-create-color-selector');
    
    if (iconSel) {
      iconSel.innerHTML = icons.map(ic => 
        `<button type="button" class="icon-option ${ic===selectedIcon?'selected':''}" data-icon="${ic}">${ic}</button>`
      ).join('');
      
      iconSel.querySelectorAll('.icon-option').forEach(btn => {
        btn.addEventListener('click', () => {
          iconSel.querySelectorAll('.icon-option').forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
        });
      });
    }
    
    if (colorSel) {
      colorSel.innerHTML = colors.map(c => 
        `<button type="button" class="color-option ${c===selectedColor?'selected':''}" data-color="${c}" style="background:${c}"></button>`
      ).join('');
      
      colorSel.querySelectorAll('.color-option').forEach(btn => {
        btn.addEventListener('click', () => {
          colorSel.querySelectorAll('.color-option').forEach(b => b.classList.remove('selected'));
          btn.classList.add('selected');
        });
      });
    }
  }
  
  setupCreateListeners() {
    const modal = document.getElementById('app-create-workspace-modal');
    const closeBtn = document.getElementById('app-create-close');
    const cancelBtn = document.getElementById('app-create-cancel');
    const form = document.getElementById('app-create-workspace-form');
    
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.closeCreateModal());
    }
    
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => this.closeCreateModal());
    }
    
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.closeCreateModal();
      });
    }
    
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.createWorkspace();
      });
    }
  }
  
  async createWorkspace() {
    const submitBtn = document.getElementById('app-create-submit');
    const originalText = submitBtn.textContent;
    
    try {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Creating...';
      
      const name = document.getElementById('app-create-name').value.trim();
      const description = document.getElementById('app-create-description').value.trim();
      const iconBtn = document.querySelector('#app-create-icon-selector .icon-option.selected');
      const colorBtn = document.querySelector('#app-create-color-selector .color-option.selected');
      const privacy = document.querySelector('input[name="app-create-privacy"]:checked')?.value || 'private';
      
      const payload = {
        name,
        description: description || undefined,
        icon: iconBtn ? iconBtn.dataset.icon : '📊',
        color: colorBtn ? colorBtn.dataset.color : '#3B82F6',
        privacy
      };
      
      const workspace = await API.post('/api/workspaces', payload);
      
      // Close modal
      this.closeCreateModal();
      
      // Switch to new workspace
      sessionStorage.setItem('currentWorkspaceId', workspace.workspace_id);
      window.location.reload();
    } catch (e) {
      console.error('Failed to create workspace:', e);
      alert('Failed to create workspace: ' + (e.message || 'Unknown error'));
      submitBtn.disabled = false;
      submitBtn.textContent = originalText;
    }
  }
  
  closeCreateModal() {
    const modal = document.getElementById('app-create-workspace-modal');
    if (modal) {
      modal.classList.remove('show');
      document.body.classList.remove('modal-open');
    }
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
