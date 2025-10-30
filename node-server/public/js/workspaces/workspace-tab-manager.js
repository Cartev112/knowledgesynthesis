/**
 * Workspace Tab Manager
 * Adapts the existing workspaces.js module for tab integration
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
    
    // Auth is already handled by main app, so we skip the workspaces.js auth check
    // by temporarily overriding the checkAuth method
    const originalCheckAuth = window.WorkspacesManager?.prototype?.checkAuth;
    
    // Simply import the existing workspaces module - it auto-initializes
    await import('./workspaces.js');
    
    // Override checkAuth to skip redirect since we're already authenticated in main app
    if (window.workspacesManager) {
      window.workspacesManager.checkAuth = async function() {
        // Auth already handled by main app - just get user info
        try {
          const response = await window.API.get('/api/me');
          this.currentUser = response.user;
          // Don't try to update user-name element - it doesn't exist in tab context
        } catch (error) {
          console.error('Not authenticated:', error);
          // Don't redirect - let main app handle auth
        }
      };
      
      // Re-run init to load workspaces without auth redirect
      await window.workspacesManager.init();
    }
    
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
