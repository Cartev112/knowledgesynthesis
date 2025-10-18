/**
 * Index Panel Management
 * Handles the side panel with documents, concepts, and relationships
 */
import { state } from '../state.js';
import { API } from '../utils/api.js';

export class IndexPanelManager {
  constructor(modalManager) {
    this.modalManager = modalManager;
  }

  async populateIndex() {
    if (!state.cy) return;
    
    const nodes = state.cy.nodes();
    const edges = state.cy.edges();
    
    // Store data for filtering
    state.indexData.nodes = nodes.map(n => ({
      id: n.id(),
      label: n.data().label,
      type: n.data().type || 'Entity',
      sources: n.data().sources || []
    }));
    
    state.indexData.edges = edges.map(e => ({
      id: e.id(),
      source: state.cy.getElementById(e.data().source).data().label,
      target: state.cy.getElementById(e.data().target).data().label,
      relation: e.data().relation || 'relates to',
      sources: e.data().sources || []
    }));
    
    // Fetch documents
    try {
      const data = await API.getDocuments();
      state.indexData.documents = data.documents || [];
      
      // Initialize all documents as active by default
      if (state.activeDocuments.size === 0) {
        state.indexData.documents.forEach(doc => {
          state.activeDocuments.add(doc.id);
        });
      }
    } catch (e) {
      console.error('Failed to load documents for index:', e);
      state.indexData.documents = [];
    }
    
    // Update counts
    document.getElementById('index-count').textContent = 
      `${nodes.length} concepts, ${edges.length} relationships, ${state.indexData.documents.length} documents`;
    document.getElementById('concepts-count').textContent = nodes.length;
    document.getElementById('relationships-count').textContent = edges.length;
    document.getElementById('documents-count').textContent = state.indexData.documents.length;
    
    // Populate type filter dropdown
    const typeFilter = document.getElementById('index-type-filter');
    const types = new Set();
    nodes.forEach(n => types.add(n.data().type || 'Entity'));
    edges.forEach(e => types.add(e.data().relation || 'relates to'));
    
    typeFilter.innerHTML = '<option value="">All Types</option>' + 
      Array.from(types).sort().map(t => `<option value="${t}">${t}</option>`).join('');
    
    // Render items
    this.renderIndexItems();
  }
  
  renderIndexItems() {
    const viewFilter = document.getElementById('index-view-filter').value;
    const typeFilter = document.getElementById('index-type-filter').value;
    
    // Show/hide sections based on view filter
    document.getElementById('documents-section').style.display = 
      (viewFilter === 'all' || viewFilter === 'documents') ? 'block' : 'none';
    document.getElementById('concepts-section').style.display = 
      (viewFilter === 'all' || viewFilter === 'concepts') ? 'block' : 'none';
    document.getElementById('relationships-section').style.display = 
      (viewFilter === 'all' || viewFilter === 'relationships') ? 'block' : 'none';
    
    // Render documents
    const documentsList = document.getElementById('documents-list');
    if (documentsList) {
      documentsList.innerHTML = '';
      
      (state.indexData.documents || []).forEach(doc => {
        const div = document.createElement('div');
        div.className = 'doc-item';
        if (state.activeDocuments.has(doc.id)) {
          div.classList.add('active');
        }
        
        const toggleDiv = document.createElement('div');
        toggleDiv.className = 'doc-toggle';
        toggleDiv.textContent = state.activeDocuments.has(doc.id) ? '✓' : '';
        toggleDiv.onclick = (e) => {
          e.stopPropagation();
          this.toggleDocument(doc.id);
        };
        
        const nameDiv = document.createElement('div');
        nameDiv.className = 'doc-name';
        nameDiv.textContent = doc.title || doc.id;
        nameDiv.onclick = (e) => {
          e.stopPropagation();
          this.modalManager.showDocumentModal(doc.id);
        };
        
        div.appendChild(toggleDiv);
        div.appendChild(nameDiv);
        
        div.onmouseenter = () => this.highlightDocumentElements(doc.id, true);
        div.onmouseleave = () => this.highlightDocumentElements(doc.id, false);
        
        documentsList.appendChild(div);
      });
    }
    
    // Filter and render concepts
    const conceptsList = document.getElementById('concepts-list');
    conceptsList.innerHTML = '';
    
    const filteredNodes = state.indexData.nodes.filter(n => 
      !typeFilter || n.type === typeFilter
    );
    
    filteredNodes.forEach(node => {
      const li = document.createElement('li');
      li.className = 'index-item';
      li.innerHTML = `${node.label}<span class="index-item-type">${node.type}</span>`;
      li.onclick = () => this.highlightAndZoomToNode(node.id);
      conceptsList.appendChild(li);
    });
    
    document.getElementById('concepts-count').textContent = filteredNodes.length;
    
    // Filter and render relationships
    const relsList = document.getElementById('relationships-list');
    relsList.innerHTML = '';
    
    const filteredEdges = state.indexData.edges.filter(e => 
      !typeFilter || e.relation === typeFilter
    );
    
    filteredEdges.forEach(edge => {
      const div = document.createElement('div');
      div.className = 'index-relationship';
      div.innerHTML = `${edge.source}<span class="rel-arrow">→</span>${edge.target}`;
      div.title = edge.relation;
      div.style.cursor = 'pointer';
      div.onclick = () => {
        console.log('Clicked edge:', edge.id, edge);
        this.highlightAndZoomToEdge(edge.id);
      };
      relsList.appendChild(div);
    });
    
    document.getElementById('relationships-count').textContent = filteredEdges.length;
  }
  
  highlightDocumentElements(docId, highlight) {
    if (!state.cy) return;
    
    state.cy.elements().forEach(el => {
      const sources = el.data().sources || [];
      const hasDoc = sources.some(s => (typeof s === 'object' ? s.id : s) === docId);
      
      if (hasDoc) {
        if (highlight) {
          el.addClass('highlighted');
        } else {
          el.removeClass('highlighted');
        }
      }
    });
  }
  
  toggleDocument(docId) {
    if (state.activeDocuments.has(docId)) {
      state.activeDocuments.delete(docId);
    } else {
      state.activeDocuments.add(docId);
    }
    
    this.applyDocumentFilter();
    this.renderIndexItems();
  }
  
  applyDocumentFilter() {
    if (!state.cy) return;
    
    // If all documents are active, show everything
    if (state.activeDocuments.size === state.indexData.documents.length) {
      state.cy.elements().style('display', 'element');
      return;
    }
    
    // Filter nodes
    state.cy.nodes().forEach(node => {
      const sources = node.data().sources || [];
      const hasActiveDoc = sources.some(s => {
        const sourceId = typeof s === 'object' ? s.id : s;
        return state.activeDocuments.has(sourceId);
      });
      
      node.style('display', hasActiveDoc ? 'element' : 'none');
    });
    
    // Filter edges
    state.cy.edges().forEach(edge => {
      const sources = edge.data().sources || [];
      const hasActiveDoc = sources.some(s => {
        const sourceId = typeof s === 'object' ? s.id : s;
        return state.activeDocuments.has(sourceId);
      });
      
      const sourceNode = state.cy.getElementById(edge.data().source);
      const targetNode = state.cy.getElementById(edge.data().target);
      const endpointsVisible = sourceNode.style('display') === 'element' && targetNode.style('display') === 'element';
      
      edge.style('display', (hasActiveDoc && endpointsVisible) ? 'element' : 'none');
    });
  }
  
  highlightAndZoomToNode(nodeId) {
    if (!state.cy) return;
    
    const node = state.cy.getElementById(nodeId);
    if (!node || node.length === 0) return;
    
    // Clear previous highlights
    this.clearAllHighlights();
    
    // Highlight in index
    const items = document.querySelectorAll('.index-item');
    items.forEach(item => {
      if (item.textContent.includes(node.data().label)) {
        item.classList.add('highlighted');
      }
    });
    
    // Highlight and zoom in graph
    state.cy.elements().removeClass('highlighted');
    node.addClass('highlighted');
    state.cy.animate({
      center: { eles: node },
      zoom: 2,
      duration: 500
    });
  }
  
  highlightAndZoomToEdge(edgeId) {
    console.log('highlightAndZoomToEdge called with:', edgeId);
    if (!state.cy || !edgeId) {
      console.warn('Missing cy or edgeId:', { cy: !!state.cy, edgeId });
      return;
    }
    
    let edge = state.cy.getElementById(edgeId);
    console.log('Edge lookup by ID:', edge.length > 0 ? 'found' : 'not found');
    
    // If not found by ID, try to find by source-target pattern
    if (edge.length === 0 && typeof edgeId === 'string' && edgeId.includes('-')) {
      const [sourceId, targetId] = edgeId.split('-');
      console.log('Trying to find edge by source-target:', { sourceId, targetId });
      edge = state.cy.edges().filter(e => {
        return e.data('source') === sourceId && e.data('target') === targetId;
      }).first();
      console.log('Edge lookup by source-target:', edge.length > 0 ? 'found' : 'not found');
    }
    
    if (!edge || edge.length === 0) {
      console.warn('Could not find edge with ID:', edgeId);
      console.log('Available edges:', state.cy.edges().map(e => ({ id: e.id(), source: e.data('source'), target: e.data('target') })));
      return;
    }
    
    // Clear previous highlights
    this.clearAllHighlights();
    
    // Highlight source and target nodes
    const source = edge.source();
    const target = edge.target();
    state.cy.elements().removeClass('highlighted');
    source.addClass('highlighted');
    target.addClass('highlighted');
    
    // Zoom to show both nodes and the edge
    state.cy.animate({
      fit: { eles: edge.union(source).union(target), padding: 100 },
      duration: 500
    });
  }
  
  clearAllHighlights() {
    if (!state.cy) return;
    
    document.querySelectorAll('.index-item').forEach(item => {
      item.classList.remove('highlighted');
    });
    
    state.cy.elements().removeClass('highlighted neighbor');
  }
}
