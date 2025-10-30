/**
 * Workspace Tab Manager
 * Simply loads the existing workspaces.js module which handles everything
 */

class WorkspaceTabManager {
  constructor() {
    this.initialized = false;
  }

  async init() {
    if (this.initialized) {
      // Just refresh if already loaded
      if (window.workspacesManager) {
        await window.workspacesManager.loadWorkspaces();
      }
      return;
    }
    
    console.log('🚀 Loading existing WorkspacesManager');
    
    // Simply import the existing workspaces module - it auto-initializes
    await import('./workspaces.js');
    
    this.initialized = true;
  }

  async loadWorkspaces() {
    if (window.workspacesManager) {
      await window.workspacesManager.loadWorkspaces();
    }
  }
}

// Export
export { WorkspaceTabManager };
