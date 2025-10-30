/**
 * Index Panel Management
 * Handles the side panel with documents, concepts, and relationships
 */
import { state } from '../state.js';
import { API } from '../utils/api.js';

export class IndexPanelManager {
  constructor(modalManager) {
    this.modalManager = modalManager;
    this.conceptsPage = 1;
    this.relsPage = 1;
    this.pageSize = 20;
    this.searchTerm = '';
    this.collapsedSections = new Set(); // Track collapsed sections
    this.setupSearchHandlers();
  }
  
  setupSearchHandlers() {
    // Wait for DOM to be ready
    if (typeof document !== 'undefined') {
      setTimeout(() => {
        const searchInput = document.getElementById('index-search');
        if (searchInput) {
          searchInput.addEventListener('input', (e) => {
            this.searchTerm = e.target.value.toLowerCase();
            state.filterStates.searchTerm = this.searchTerm;
            this.conceptsPage = 1;
            this.relsPage = 1;
            this.renderIndexItems();
          });
        }
        
        // Save filter states when changed
        const viewFilter = document.getElementById('index-view-filter');
        if (viewFilter) {
          viewFilter.addEventListener('change', (e) => {
            state.filterStates.viewFilter = e.target.value;
          });
        }
        
        const typeFilter = document.getElementById('index-type-filter');
        if (typeFilter) {
          typeFilter.addEventListener('change', (e) => {
            state.filterStates.typeFilter = e.target.value;
          });
        }
        
        const verifiedCheckbox = document.getElementById('verified-only-checkbox');
        if (verifiedCheckbox) {
          verifiedCheckbox.addEventListener('change', (e) => {
            state.filterStates.verifiedOnly = e.target.checked;
          });
        }
      }, 100);
    }
  }

  async populateIndex() {
    if (!state.cy) return;
    
    const nodes = state.cy.nodes();
    const edges = state.cy.edges();
    const workspaceId = sessionStorage.getItem('currentWorkspaceId');
    
    // Store data for filtering
    // We'll populate after fetching documents so workspace filtering can apply
    
    // Fetch documents
    try {
      const data = await API.getDocuments();
      state.indexData.documents = data.documents || [];
    } catch (e) {
      console.error('Failed to load documents for index:', e);
      state.indexData.documents = [];
    }

    // Build lookup of workspace documents; empty set implies global view
    const workspaceDocIds = new Set((state.indexData.documents || []).map(doc => doc.id));
    const includeAllDocs = workspaceDocIds.size === 0;

    // Reset active documents to the current workspace set
    state.activeDocuments = new Set(workspaceDocIds);
    if (includeAllDocs && state.indexData.documents.length === 0) {
      // Global view without explicit workspace: include all doc ids found on nodes/edges as we encounter them
      state.activeDocuments = new Set();
    }

    const belongsToWorkspace = (sources = []) => {
      if (includeAllDocs) return true;
      if (!sources || sources.length === 0) return true; // allow type/context nodes without explicit document sources
      return sources.some((source) => {
        if (!source) return false;
        const sourceId = typeof source === 'object' ? source.id : source;
        return workspaceDocIds.has(sourceId);
      });
    };

    state.indexData.nodes = nodes.reduce((acc, n) => {
      const sources = n.data().sources || [];
      if (!belongsToWorkspace(sources)) return acc;

    const entry = {
      id: n.id(),
      label: n.data().label,
      type: n.data().type || 'Concept',
      labels: n.data().labels || [],
      types: n.data().types || [],
      sources
    };
      acc.push(entry);
      if (includeAllDocs) {
        sources.forEach((src) => {
          const srcId = typeof src === 'object' ? src.id : src;
          if (srcId) {
            state.activeDocuments.add(srcId);
          }
        });
      }
      return acc;
    }, []);
    
    const allowedNodeIds = new Set(state.indexData.nodes.map(n => n.id));
    
    state.indexData.edges = edges.reduce((acc, e) => {
      const data = e.data();
      const sources = data.sources || [];
      if (!belongsToWorkspace(sources)) return acc;

      if (!allowedNodeIds.has(data.source) || !allowedNodeIds.has(data.target)) {
        return acc;
      }

      const sourceNode = state.cy.getElementById(data.source);
      const targetNode = state.cy.getElementById(data.target);
      const sourceLabel = sourceNode && sourceNode.length ? (sourceNode.data().label || data.source) : data.source;
      const targetLabel = targetNode && targetNode.length ? (targetNode.data().label || data.target) : data.target;

      acc.push({
        id: e.id(),
        source: sourceLabel,
        target: targetLabel,
        relation: data.relation || 'relates to',
        sources
      });

      if (includeAllDocs) {
        sources.forEach((src) => {
          const srcId = typeof src === 'object' ? src.id : src;
          if (srcId) {
            state.activeDocuments.add(srcId);
          }
        });
      }

      return acc;
    }, []);
    
    // Ensure active document set only contains docs present in current workspace view
    if (!includeAllDocs) {
      state.activeDocuments = new Set(workspaceDocIds);
    }
    
    // Update counts
    document.getElementById('index-count').textContent = 
      `${state.indexData.nodes.length} concepts, ${state.indexData.edges.length} relationships, ${state.indexData.documents.length} documents`;
    document.getElementById('concepts-count').textContent = state.indexData.nodes.length;
    document.getElementById('relationships-count').textContent = state.indexData.edges.length;
    document.getElementById('documents-count').textContent = state.indexData.documents.length;
    
    // Populate type filter dropdown
    const typeFilter = document.getElementById('index-type-filter');
    const types = new Set();
    state.indexData.nodes.forEach(n => types.add(n.type || 'Entity'));
    state.indexData.edges.forEach(e => types.add(e.relation || 'relates to'));
    
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
    
    // Filter and render concepts with search and pagination
    const conceptsList = document.getElementById('concepts-list');
    conceptsList.innerHTML = '';
    
    let filteredNodes = state.indexData.nodes.filter(n => {
      const matchesType = !typeFilter || n.type === typeFilter;
      const matchesSearch = !this.searchTerm || 
        n.label.toLowerCase().includes(this.searchTerm) ||
        n.type.toLowerCase().includes(this.searchTerm);
      return matchesType && matchesSearch;
    });
    
    const totalConcepts = filteredNodes.length;
    const showing = Math.min(this.conceptsPage * this.pageSize, totalConcepts);
    const displayNodes = filteredNodes.slice(0, showing);
    
    displayNodes.forEach(node => {
      const li = document.createElement('li');
      li.className = 'index-item';
      li.innerHTML = `${node.label}<span class="index-item-type">${node.type}</span>`;
      li.onclick = () => this.highlightAndZoomToNode(node.id);
      li.onmouseenter = () => {
        // 2D hover highlight
        if (state.cy) {
          const n = state.cy.getElementById(node.id);
          if (n && n.length) n.addClass('highlighted');
        }
        // 3D hover highlight
        if (window.appManager?.is3D && window.appManager?.graph3D) {
          window.appManager.graph3D.highlightNodeById(node.id, true);
        }
      };
      li.onmouseleave = () => {
        if (state.cy) {
          const n = state.cy.getElementById(node.id);
          if (n && n.length) n.removeClass('highlighted');
        }
        if (window.appManager?.is3D && window.appManager?.graph3D) {
          window.appManager.graph3D.highlightNodeById(node.id, false);
        }
      };
      conceptsList.appendChild(li);
    });
    
    // Add "Show More" button if needed
    if (showing < totalConcepts) {
      const showMoreBtn = document.createElement('button');
      showMoreBtn.className = 'index-show-more';
      showMoreBtn.textContent = `Show More (${totalConcepts - showing} remaining)`;
      showMoreBtn.onclick = () => {
        this.conceptsPage++;
        this.renderIndexItems();
      };
      conceptsList.appendChild(showMoreBtn);
    }
    
    document.getElementById('concepts-count').textContent = `${showing}/${totalConcepts}`;
    
    // Filter and render relationships with search and pagination
    const relsList = document.getElementById('relationships-list');
    relsList.innerHTML = '';
    
    let filteredEdges = state.indexData.edges.filter(e => {
      const matchesType = !typeFilter || e.relation === typeFilter;
      const matchesSearch = !this.searchTerm || 
        e.source.toLowerCase().includes(this.searchTerm) ||
        e.target.toLowerCase().includes(this.searchTerm) ||
        e.relation.toLowerCase().includes(this.searchTerm);
      return matchesType && matchesSearch;
    });
    
    const totalRels = filteredEdges.length;
    const showingRels = Math.min(this.relsPage * this.pageSize, totalRels);
    const displayEdges = filteredEdges.slice(0, showingRels);

    displayEdges.forEach(edge => {
      const div = document.createElement('div');
      div.className = 'index-relationship';

      const sourceSpan = document.createElement('span');
      sourceSpan.className = 'rel-source';
      sourceSpan.textContent = edge.source;

      const relationSpan = document.createElement('span');
      relationSpan.className = 'rel-label';
      relationSpan.textContent = `[${edge.relation}]`;

      const targetSpan = document.createElement('span');
      targetSpan.className = 'rel-target';
      targetSpan.textContent = edge.target;

      div.append(sourceSpan, relationSpan, targetSpan);
      div.title = `${edge.source} [${edge.relation}] ${edge.target}`;
      div.style.cursor = 'pointer';
      div.onclick = () => {
        console.log('Clicked edge:', edge.id, edge);
        this.highlightAndZoomToEdge(edge.id);
      };
      relsList.appendChild(div);
    });
    
    
    // Add "Show More" button if needed
    if (showingRels < totalRels) {
      const showMoreBtn = document.createElement('button');
      showMoreBtn.className = 'index-show-more';
      showMoreBtn.textContent = `Show More (${totalRels - showingRels} remaining)`;
      showMoreBtn.onclick = () => {
        this.relsPage++;
        this.renderIndexItems();
      };
      relsList.appendChild(showMoreBtn);
    }
    
    document.getElementById('relationships-count').textContent = `${showingRels}/${totalRels}`;
  }
  
  highlightDocumentElements(docId, highlight) {
    if (state.cy) {
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
    // 3D equivalent
    if (window.appManager?.is3D && window.appManager?.graph3D) {
      window.appManager.graph3D.highlightDocumentEntities(docId, highlight);
    }
  }
  
  toggleDocument(docId) {
    if (state.activeDocuments.has(docId)) {
      state.activeDocuments.delete(docId);
    } else {
      state.activeDocuments.add(docId);
    }
    
    this.applyDocumentFilter();
    if (window.appManager?.is3D && window.appManager?.graph3D) {
      window.appManager.graph3D.applyDocumentFilter3D();
    }
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
      const hasActiveDoc = sources.length === 0 || sources.some(s => {
        const sourceId = typeof s === 'object' ? s.id : s;
        return state.activeDocuments.has(sourceId);
      });
      
      node.style('display', hasActiveDoc ? 'element' : 'none');
    });
    
    // Filter edges
    state.cy.edges().forEach(edge => {
      const sources = edge.data().sources || [];
      const hasActiveDoc = sources.length === 0 || sources.some(s => {
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
    if (state.cy) {
      const node = state.cy.getElementById(nodeId);
      if (node && node.length !== 0) {
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
    }
    // 3D zoom as well
    if (window.appManager?.is3D && window.appManager?.graph3D) {
      window.appManager.graph3D.focusNodeById(nodeId);
    }
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
  
  toggleSection(sectionName) {
    const section = document.getElementById(`${sectionName}-section`);
    if (!section) return;
    
    const content = section.querySelector('.index-section-content');
    const arrow = section.querySelector('.section-arrow');
    
    if (this.collapsedSections.has(sectionName)) {
      // Expand
      this.collapsedSections.delete(sectionName);
      content.classList.remove('collapsed');
      if (arrow) arrow.textContent = 'Γû╝';
    } else {
      // Collapse
      this.collapsedSections.add(sectionName);
      content.classList.add('collapsed');
      if (arrow) arrow.textContent = 'Γû╢';
    }
  }
}
