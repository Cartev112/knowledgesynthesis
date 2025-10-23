/**
 * View Filter Component
 * Handles filtering graph view by users, entity types, dates, etc.
 */

import { API } from '../utils/api.js';

class ViewFilter {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.currentWorkspace = null;
    this.workspaceMembers = [];
    this.filters = {
      viewMode: 'workspace', // 'my_content', 'workspace', 'collaborative', 'global'
      userIds: [],
      entityTypes: [],
      dateRange: null,
      significanceRange: { min: 1, max: 5 }
    };
    
    this.init();
  }

  async init() {
    if (!this.container) {
      console.warn('View filter container not found');
      return;
    }

    // Listen for workspace changes
    window.addEventListener('workspaceChanged', (e) => {
      this.currentWorkspace = e.detail.workspace;
      this.loadWorkspaceMembers();
      this.render();
    });

    // Get current workspace
    const workspaceId = sessionStorage.getItem('currentWorkspaceId');
    if (workspaceId) {
      await this.loadWorkspace(workspaceId);
    }

    this.render();
    this.setupEventListeners();
  }

  async loadWorkspace(workspaceId) {
    try {
      this.currentWorkspace = await API.get(`/api/workspaces/${workspaceId}`);
      this.workspaceMembers = this.currentWorkspace.members || [];
    } catch (error) {
      console.error('Failed to load workspace:', error);
    }
  }

  async loadWorkspaceMembers() {
    if (!this.currentWorkspace) {
      this.workspaceMembers = [];
      return;
    }

    try {
      const workspace = await API.get(`/api/workspaces/${this.currentWorkspace.workspace_id}`);
      this.workspaceMembers = workspace.members || [];
    } catch (error) {
      console.error('Failed to load workspace members:', error);
      this.workspaceMembers = [];
    }
  }

  render() {
    const isGlobalView = !this.currentWorkspace;
    const hasMembers = this.workspaceMembers.length > 1;

    this.container.innerHTML = `
      <div class="view-filter-panel">
        <div class="filter-header">
          <h3>View Filters</h3>
          <button class="close-button" id="close-filter-panel">✕</button>
        </div>

        <div class="filter-section">
          <label class="filter-label">Scope</label>
          <div class="filter-options">
            ${!isGlobalView ? `
              <label class="filter-option">
                <input type="radio" name="viewMode" value="workspace" ${this.filters.viewMode === 'workspace' ? 'checked' : ''}>
                <span class="option-label">
                  <strong>Workspace View</strong>
                  <small>All content in workspace</small>
                </span>
              </label>

              <label class="filter-option">
                <input type="radio" name="viewMode" value="my_content" ${this.filters.viewMode === 'my_content' ? 'checked' : ''}>
                <span class="option-label">
                  <strong>My Content Only</strong>
                  <small>Only what I created</small>
                </span>
              </label>

              ${hasMembers ? `
                <label class="filter-option">
                  <input type="radio" name="viewMode" value="collaborative" ${this.filters.viewMode === 'collaborative' ? 'checked' : ''}>
                  <span class="option-label">
                    <strong>Collaborative View</strong>
                    <small>Selected users</small>
                  </span>
                </label>
              ` : ''}
            ` : `
              <label class="filter-option">
                <input type="radio" name="viewMode" value="global" checked>
                <span class="option-label">
                  <strong>Global View</strong>
                  <small>Entire database</small>
                </span>
              </label>
            `}
          </div>
        </div>

        ${this.filters.viewMode === 'collaborative' && hasMembers ? `
          <div class="filter-section">
            <label class="filter-label">Select Users</label>
            <div class="user-checkboxes">
              ${this.workspaceMembers.map(member => `
                <label class="checkbox-label">
                  <input type="checkbox" 
                         class="user-checkbox" 
                         value="${member.user_id}"
                         ${this.filters.userIds.includes(member.user_id) ? 'checked' : ''}>
                  <span>${this.escapeHtml(member.user_first_name)} ${this.escapeHtml(member.user_last_name)}</span>
                  ${member.role === 'owner' ? '<span class="role-badge">Owner</span>' : ''}
                </label>
              `).join('')}
            </div>
            <div class="checkbox-actions">
              <button class="text-button" id="select-all-users">Select All</button>
              <button class="text-button" id="clear-all-users">Clear All</button>
            </div>
          </div>
        ` : ''}

        <div class="filter-section">
          <label class="filter-label">Entity Types</label>
          <div class="entity-type-chips">
            ${this.getCommonEntityTypes().map(type => `
              <label class="chip-label">
                <input type="checkbox" class="entity-type-checkbox" value="${type}">
                <span class="chip">${type}</span>
              </label>
            `).join('')}
          </div>
        </div>

        <div class="filter-section">
          <label class="filter-label">Date Range</label>
          <div class="date-inputs">
            <input type="date" id="date-from" placeholder="From">
            <input type="date" id="date-to" placeholder="To">
          </div>
        </div>

        <div class="filter-section">
          <label class="filter-label">Significance</label>
          <div class="range-slider">
            <div class="range-values">
              <span>Min: <strong id="sig-min-value">1</strong></span>
              <span>Max: <strong id="sig-max-value">5</strong></span>
            </div>
            <input type="range" id="sig-min" min="1" max="5" value="1" step="1">
            <input type="range" id="sig-max" min="1" max="5" value="5" step="1">
          </div>
        </div>

        <div class="filter-actions">
          <button class="button button-secondary" id="reset-filters">Reset</button>
          <button class="button button-primary" id="apply-filters">Apply Filters</button>
        </div>

        <div class="filter-stats" id="filter-stats">
          <small>Loading stats...</small>
        </div>
      </div>
    `;
  }

  setupEventListeners() {
    // Close button
    const closeButton = document.getElementById('close-filter-panel');
    if (closeButton) {
      closeButton.addEventListener('click', () => {
        this.container.style.display = 'none';
      });
    }

    // View mode radio buttons
    document.querySelectorAll('input[name="viewMode"]').forEach(radio => {
      radio.addEventListener('change', (e) => {
        this.filters.viewMode = e.target.value;
        this.render();
        this.setupEventListeners();
      });
    });

    // User checkboxes
    document.querySelectorAll('.user-checkbox').forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        const userId = e.target.value;
        if (e.target.checked) {
          if (!this.filters.userIds.includes(userId)) {
            this.filters.userIds.push(userId);
          }
        } else {
          this.filters.userIds = this.filters.userIds.filter(id => id !== userId);
        }
      });
    });

    // Select/Clear all users
    const selectAllBtn = document.getElementById('select-all-users');
    if (selectAllBtn) {
      selectAllBtn.addEventListener('click', () => {
        document.querySelectorAll('.user-checkbox').forEach(cb => {
          cb.checked = true;
          const userId = cb.value;
          if (!this.filters.userIds.includes(userId)) {
            this.filters.userIds.push(userId);
          }
        });
      });
    }

    const clearAllBtn = document.getElementById('clear-all-users');
    if (clearAllBtn) {
      clearAllBtn.addEventListener('click', () => {
        document.querySelectorAll('.user-checkbox').forEach(cb => {
          cb.checked = false;
        });
        this.filters.userIds = [];
      });
    }

    // Entity type checkboxes
    document.querySelectorAll('.entity-type-checkbox').forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        const type = e.target.value;
        if (e.target.checked) {
          if (!this.filters.entityTypes.includes(type)) {
            this.filters.entityTypes.push(type);
          }
        } else {
          this.filters.entityTypes = this.filters.entityTypes.filter(t => t !== type);
        }
      });
    });

    // Significance sliders
    const sigMin = document.getElementById('sig-min');
    const sigMax = document.getElementById('sig-max');
    const sigMinValue = document.getElementById('sig-min-value');
    const sigMaxValue = document.getElementById('sig-max-value');

    if (sigMin && sigMax) {
      sigMin.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        if (value > parseInt(sigMax.value)) {
          sigMax.value = value;
        }
        sigMinValue.textContent = value;
        this.filters.significanceRange.min = value;
      });

      sigMax.addEventListener('input', (e) => {
        const value = parseInt(e.target.value);
        if (value < parseInt(sigMin.value)) {
          sigMin.value = value;
        }
        sigMaxValue.textContent = value;
        this.filters.significanceRange.max = value;
      });
    }

    // Reset button
    const resetBtn = document.getElementById('reset-filters');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        this.resetFilters();
      });
    }

    // Apply button
    const applyBtn = document.getElementById('apply-filters');
    if (applyBtn) {
      applyBtn.addEventListener('click', () => {
        this.applyFilters();
      });
    }
  }

  getCommonEntityTypes() {
    return ['Gene', 'Protein', 'Disease', 'Drug', 'Pathway', 'Method', 'Concept', 'Cell_Type'];
  }

  resetFilters() {
    this.filters = {
      viewMode: 'workspace',
      userIds: [],
      entityTypes: [],
      dateRange: null,
      significanceRange: { min: 1, max: 5 }
    };
    this.render();
    this.setupEventListeners();
    this.applyFilters();
  }

  applyFilters() {
    // Emit filter change event
    const event = new CustomEvent('filtersChanged', {
      detail: {
        filters: this.filters,
        workspaceId: this.currentWorkspace?.workspace_id || null
      }
    });
    window.dispatchEvent(event);

    // Update stats
    this.updateStats();
  }

  async updateStats() {
    const statsEl = document.getElementById('filter-stats');
    if (!statsEl) return;

    statsEl.innerHTML = '<small>Calculating stats...</small>';

    // TODO: Implement actual stats calculation based on filters
    // For now, just show filter summary
    const summary = [];
    
    if (this.filters.viewMode === 'my_content') {
      summary.push('My content only');
    } else if (this.filters.viewMode === 'collaborative') {
      summary.push(`${this.filters.userIds.length} users selected`);
    }
    
    if (this.filters.entityTypes.length > 0) {
      summary.push(`${this.filters.entityTypes.length} entity types`);
    }

    statsEl.innerHTML = `<small>${summary.join(' • ') || 'No filters applied'}</small>`;
  }

  getFilters() {
    return this.filters;
  }

  show() {
    this.container.style.display = 'block';
  }

  hide() {
    this.container.style.display = 'none';
  }

  toggle() {
    if (this.container.style.display === 'none') {
      this.show();
    } else {
      this.hide();
    }
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

export default ViewFilter;
