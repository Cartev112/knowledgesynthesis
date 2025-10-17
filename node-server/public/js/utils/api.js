/**
 * API Wrapper for Backend Communication
 */
export class API {
  static async request(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.message || `HTTP ${response.status}`);
    }
    
    return response.json();
  }
  
  static async get(url) {
    return this.request(url);
  }
  
  static async post(url, data) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  static async put(url, data) {
    return this.request(url, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }
  
  static async delete(url) {
    return this.request(url, {
      method: 'DELETE'
    });
  }
  
  // Specific API endpoints
  static async getCurrentUser() {
    return this.get('/api/me');
  }
  
  static async logout() {
    return this.post('/api/logout', {});
  }
  
  static async getDocuments() {
    return this.get('/api/query/documents');
  }
  
  static async getAllGraph() {
    const timestamp = new Date().getTime();
    return this.get(`/api/query/all?t=${timestamp}`);
  }
  
  static async searchConcept(name, verifiedOnly = false) {
    return this.get(`/api/query/search/concept?name=${encodeURIComponent(name)}&verified_only=${verifiedOnly}`);
  }
  
  static async getSubgraph(nodeIds) {
    return this.post('/api/query/subgraph', { node_ids: nodeIds });
  }
  
  static async ingestPDF(formData) {
    const response = await fetch('/api/ingest/pdf', {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || 'Failed to ingest PDF');
    }
    
    return response.json();
  }
  
  static async ingestText(data) {
    return this.post('/api/ingest/text', data);
  }
}
