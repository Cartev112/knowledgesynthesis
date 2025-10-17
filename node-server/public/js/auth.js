/**
 * Authentication Manager
 */
import { API } from './utils/api.js';
import { state } from './state.js';

export class AuthManager {
  async checkAuth() {
    try {
      const data = await API.getCurrentUser();
      state.currentUser = data.user;
      const usernameEl = document.getElementById('username');
      if (usernameEl) {
        // Display first name, or full name, or email, or fallback to 'User'
        const displayName = state.currentUser.first_name || 
                           `${state.currentUser.first_name || ''} ${state.currentUser.last_name || ''}`.trim() ||
                           state.currentUser.email ||
                           state.currentUser.username || 
                           state.currentUser.user_id || 
                           'User';
        usernameEl.textContent = displayName;
      }
    } catch (e) {
      console.error('Auth check failed:', e);
      window.location.href = '/login';
    }
  }
  
  async logout() {
    try {
      await API.logout();
    } catch (e) {
      console.error('Logout failed:', e);
    }
    window.location.href = '/login';
  }
}
