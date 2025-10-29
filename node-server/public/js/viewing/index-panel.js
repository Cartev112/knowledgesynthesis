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
    this.searchTerm = state.filterStates?.searchTerm || '';
    this.instances = [];
    this.collapsedSections = new Set(); // Track collapsed sections per container
    this.setupSearchHandlers();
  }
  
  setupSearchHandlers() {
    if (typeof document === 'undefined') return;
    setTimeout(() => {
      this.initializeInstances();
    }, 100);
  }

  initializeInstances() {
    if (typeof document === 'undefined') return;
    const containers = Array.from(document.querySelectorAll('[data-index-container]'));
    let added = false;

    containers.forEach(container => {
      if (this.instances.some(inst => inst.container === container)) {
        return;
      }
      const instance = this.createInstance(container);
      if (instance) {
        this.instances.push(instance);
        this.attachInstanceListeners(instance);
        added = true;
      }
    });

    if (added) {
      this.syncInstanceInputs();
      this.renderIndexItems();
    }
  }

  createInstance(container) {
    if (!container) return null;
    return {
      container,
      key: container.dataset.indexId || container.dataset.indexContainer || `instance-${this.instances.length}`,
      searchInput: container.querySelector('[data-index-search]'),
      viewFilter: container.querySelector('[data-index-view-filter]'),
      typeFilter: container.querySelector('[data-index-type-filter]'),
      verifiedCheckbox: container.querySelector('[data-index-verified]'),
      indexCount: container.querySelector('[data-index-count]'),
      documentsSection: container.querySelector('[data-section=\"documents\"]'),
      conceptsSection: container.querySelector('[data-section=\"concepts\"]'),
      relationshipsSection: container.querySelector('[data-section=\"relationships\"]'),
      documentsList: container.querySelector('[data-documents-list]'),
      conceptsList: container.querySelector('[data-concepts-list]'),
      relationshipsList: container.querySelector('[data-relationships-list]'),
      documentsCount: container.querySelector('[data-documents-count]'),
      conceptsCount: container.querySelector('[data-concepts-count]'),
      relationshipsCount: container.querySelector('[data-relationships-count]')
    };
  }

  attachInstanceListeners(instance) {
    if (!instance) return;

    if (instance.searchInput && !instance.searchInput.dataset.indexListenerBound) {
      instance.searchInput.addEventListener('input', (e) => {
        this.searchTerm = e.target.value;
        state.filterStates.searchTerm = this.searchTerm;
        this.conceptsPage = 1;
        this.relsPage = 1;
        this.syncInstanceInputs('search');
        this.renderIndexItems();
      });
      instance.searchInput.dataset.indexListenerBound = 'true';
    }

    if (instance.viewFilter && !instance.viewFilter.dataset.indexListenerBound) {
      instance.viewFilter.addEventListener('change', (e) => {
        state.filterStates.viewFilter = e.target.value;
        this.conceptsPage = 1;
        this.relsPage = 1;
        this.syncInstanceInputs('viewFilter');
        this.renderIndexItems();
      });
      instance.viewFilter.dataset.indexListenerBound = 'true';
    }

    if (instance.typeFilter && !instance.typeFilter.dataset.indexListenerBound) {
      instance.typeFilter.addEventListener('change', (e) => {
        state.filterStates.typeFilter = e.target.value;
        this.conceptsPage = 1;
        this.relsPage = 1;
        this.syncInstanceInputs('typeFilter');
        this.renderIndexItems();
      });
      instance.typeFilter.dataset.indexListenerBound = 'true';
    }

    if (instance.verifiedCheckbox && !instance.verifiedCheckbox.dataset.indexListenerBound) {
      instance.verifiedCheckbox.addEventListener('change', (e) => {
        state.filterStates.verifiedOnly = e.target.checked;
        this.renderIndexItems();
      });
      instance.verifiedCheckbox.dataset.indexListenerBound = 'true';
    }
  }

  syncInstanceInputs(changedField) {
    const viewFilter = state.filterStates.viewFilter || 'all';
    const typeFilter = state.filterStates.typeFilter || '';

    this.instances.forEach(instance => {
      if (instance.searchInput && (!changedField || changedField === 'search')) {
        if (instance.searchInput.value !== this.searchTerm) {
          instance.searchInput.value = this.searchTerm;
        }
      }

      if (instance.viewFilter && (!changedField || changedField === 'viewFilter')) {
        if (instance.viewFilter.value !== viewFilter) {
          instance.viewFilter.value = viewFilter;
        }
      }

      if (instance.typeFilter && (!changedField || changedField === 'typeFilter')) {
        if (instance.typeFilter.value !== typeFilter) {
          instance.typeFilter.value = typeFilter;
        }
      }

      if (instance.verifiedCheckbox && (!changedField || changedField === 'verifiedCheckbox')) {
        instance.verifiedCheckbox.checked = !!state.filterStates.verifiedOnly;
      }
    });
  }

  getContainerKey(container) {
    if (!container) return 'default';
    return container.dataset.indexId || container.dataset.indexContainer || 'default';
  }

  async populateIndex() {
    if (!state.cy) return;
    this.initializeInstances();

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
    
    // Update counts in each registered container
    this.instances.forEach(instance => {
      if (instance.indexCount) {
        instance.indexCount.textContent = `${nodes.length} concepts, ${edges.length} relationships, ${state.indexData.documents.length} documents`;
      }
      if (instance.conceptsCount) {
        instance.conceptsCount.textContent = nodes.length.toString();
      }
      if (instance.relationshipsCount) {
        instance.relationshipsCount.textContent = edges.length.toString();
      }
      if (instance.documentsCount) {
        instance.documentsCount.textContent = state.indexData.documents.length.toString();
      }
    });
    
    // Populate type filter dropdowns
    const types = new Set();
    nodes.forEach(n => types.add(n.data().type || 'Entity'));
    edges.forEach(e => types.add(e.data().relation || 'relates to'));
    
    const sortedTypes = Array.from(types).sort();
    const typeOptions = ['<option value="">All Types</option>', ...sortedTypes.map(t => `<option value="${t}">${t}</option>`)].join('');
    const desiredType = sortedTypes.includes(state.filterStates.typeFilter) ? state.filterStates.typeFilter : '';
    state.filterStates.typeFilter = desiredType;
    
    this.instances.forEach(instance => {
      if (instance.typeFilter) {
        instance.typeFilter.innerHTML = typeOptions;
        instance.typeFilter.value = desiredType;
      }
    });
    
    this.syncInstanceInputs();
    
    // Render items
    this.renderIndexItems();
  }
  
  renderIndexItems() {
    if (this.instances.length === 0) {
      this.initializeInstances();
      if (this.instances.length === 0) {
        return;
      }
    }

    const viewFilter = state.filterStates.viewFilter || 'all';
    const typeFilter = state.filterStates.typeFilter || '';
    const searchTerm = (this.searchTerm || '').trim().toLowerCase();

    const documents = state.indexData.documents || [];
    const nodesData = state.indexData.nodes || [];
    const edgesData = state.indexData.edges || [];

    const filteredNodes = nodesData.filter(n => {
      const matchesType = !typeFilter || n.type === typeFilter;
      const matchesSearch = !searchTerm ||
        (n.label || '').toLowerCase().includes(searchTerm) ||
        (n.type || '').toLowerCase().includes(searchTerm);
      return matchesType && matchesSearch;
    });

    const totalConcepts = filteredNodes.length;
    const showingConcepts = Math.min(this.conceptsPage * this.pageSize, totalConcepts);
    const displayNodes = filteredNodes.slice(0, showingConcepts);

    const filteredEdges = edgesData.filter(e => {
      const matchesType = !typeFilter || e.relation === typeFilter;
      const matchesSearch = !searchTerm ||
        (e.source || '').toLowerCase().includes(searchTerm) ||
        (e.target || '').toLowerCase().includes(searchTerm) ||
        (e.relation || '').toLowerCase().includes(searchTerm);
      return matchesType && matchesSearch;
    });

    const totalRels = filteredEdges.length;
    const showingRels = Math.min(this.relsPage * this.pageSize, totalRels);
    const displayEdges = filteredEdges.slice(0, showingRels);

    this.instances.forEach(instance => {
      const showDocs = viewFilter === 'all' || viewFilter === 'documents';
      const showConcepts = viewFilter === 'all' || viewFilter === 'concepts';
      const showRels = viewFilter === 'all' || viewFilter === 'relationships';

      if (instance.documentsSection) {
        instance.documentsSection.style.display = showDocs ? 'block' : 'none';
      }
      if (instance.conceptsSection) {
        instance.conceptsSection.style.display = showConcepts ? 'block' : 'none';
      }
      if (instance.relationshipsSection) {
        instance.relationshipsSection.style.display = showRels ? 'block' : 'none';
      }

      if (instance.documentsCount) {
        instance.documentsCount.textContent = documents.length.toString();
      }
      if (instance.conceptsCount) {
        instance.conceptsCount.textContent = totalConcepts === 0 ? '0/0' : `${showingConcepts}/${totalConcepts}`;
      }
      if (instance.relationshipsCount) {
        instance.relationshipsCount.textContent = totalRels === 0 ? '0/0' : `${showingRels}/${totalRels}`;
      }

      if (showDocs) {
        this.renderDocumentsList(instance, documents);
      } else if (instance.documentsList) {
        instance.documentsList.innerHTML = '';
      }

      if (showConcepts) {
        this.renderConceptsList(instance, displayNodes, totalConcepts, showingConcepts);
      } else if (instance.conceptsList) {
        instance.conceptsList.innerHTML = '';
      }

      if (showRels) {
        this.renderRelationshipsList(instance, displayEdges, totalRels, showingRels);
      } else if (instance.relationshipsList) {
        instance.relationshipsList.innerHTML = '';
      }
    });

    this.syncInstanceInputs();
  }

  renderDocumentsList(instance, documents) {
    if (!instance?.documentsList) return;
    const list = instance.documentsList;
    list.innerHTML = '';
    (documents || []).forEach(doc => {
      const div = document.createElement('div');
      div.className = 'doc-item';
      if (state.activeDocuments.has(doc.id)) {
        div.classList.add('active');
      }
      const toggleDiv = document.createElement('div');
      toggleDiv.className = 'doc-toggle';
      toggleDiv.textContent = state.activeDocuments.has(doc.id) ? '?o"' : '';
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
      list.appendChild(div);
    });
  }

  renderConceptsList(instance, nodes, totalConcepts, showingConcepts) {
    if (!instance?.conceptsList) return;
    const list = instance.conceptsList;
    list.innerHTML = '';
    (nodes || []).forEach(node => {
      const li = document.createElement('li');
      li.className = 'index-item';
      li.dataset.nodeId = node.id;
      li.innerHTML = `${node.label}<span class="index-item-type">${node.type}</span>`;
      li.onclick = () => this.highlightAndZoomToNode(node.id);
      li.onmouseenter = () => {
        if (state.cy) {
          const n = state.cy.getElementById(node.id);
          if (n && n.length) n.addClass('highlighted');
        }
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
      list.appendChild(li);
    });
    if (showingConcepts < totalConcepts) {
      const showMoreBtn = document.createElement('button');
      showMoreBtn.className = 'index-show-more';
      showMoreBtn.textContent = `Show More (${totalConcepts - showingConcepts} remaining)`;
      showMoreBtn.onclick = () => {
        this.conceptsPage++;
        this.renderIndexItems();
      };
      list.appendChild(showMoreBtn);
    }
  }

  renderRelationshipsList(instance, edges, totalRels, showingRels) {
    if (!instance?.relationshipsList) return;
    const list = instance.relationshipsList;
    list.innerHTML = '';
    (edges || []).forEach(edge => {
      const div = document.createElement('div');
      div.className = 'index-relationship';
      div.dataset.edgeId = edge.id;
      div.innerHTML = `${edge.source}<span class="rel-arrow">?+'</span>${edge.target}`;
      div.title = edge.relation;
      div.style.cursor = 'pointer';
      div.onclick = () => {
        this.highlightAndZoomToEdge(edge.id);
      };
      list.appendChild(div);
    });
    if (showingRels < totalRels) {
      const showMoreBtn = document.createElement('button');
      showMoreBtn.className = 'index-show-more';
      showMoreBtn.textContent = `Show More (${totalRels - showingRels} remaining)`;
      showMoreBtn.onclick = () => {
        this.relsPage++;
        this.renderIndexItems();
      };
      list.appendChild(showMoreBtn);
    }
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
    
    this.clearAllHighlights();
    
    const items = document.querySelectorAll('.index-item');
    items.forEach(item => {
      if (item.dataset.nodeId === nodeId) {
        item.classList.add('highlighted');
      }
    });
    
    state.cy.elements().removeClass('highlighted');
    node.addClass('highlighted');
    
    this.modalManager.showNodeModal(node.data());
    
    if (window.appManager?.is3D && window.appManager?.graph3D) {
      window.appManager.graph3D.highlightNodeById(nodeId, true);
      window.appManager.graph3D.focusNodeById(nodeId);
    }
  }
  
  highlightAndZoomToEdge(edgeId) {
    if (!state.cy || !edgeId) return;
    
    let edge = state.cy.getElementById(edgeId);
    
    if (edge.length === 0 && typeof edgeId === 'string' && edgeId.includes('-')) {
      const [sourceId, targetId] = edgeId.split('-');
      edge = state.cy.edges().filter(e => {
        return e.data('source') === sourceId && e.data('target') === targetId;
      }).first();
    }
    
    if (!edge || edge.length === 0) {
      console.warn('Could not find edge with ID:', edgeId);
      return;
    }
    
    this.clearAllHighlights();
    
    const source = edge.source();
    const target = edge.target();
    state.cy.elements().removeClass('highlighted');
    source.addClass('highlighted');
    target.addClass('highlighted');
    
    const edgeIdString = edge.id();
    document.querySelectorAll('.index-relationship').forEach(item => {
      if (item.dataset.edgeId === edgeIdString) {
        item.classList.add('highlighted');
      }
    });
    
    this.modalManager.showEdgeModal(edge.data());
  }
  
  clearAllHighlights() {
    if (!state.cy) return;
    
    document.querySelectorAll('.index-item').forEach(item => {
      item.classList.remove('highlighted');
    });
    document.querySelectorAll('.index-relationship').forEach(item => {
      item.classList.remove('highlighted');
    });
    
    state.cy.elements().removeClass('highlighted neighbor');
  }
  
  toggleSection(triggerEl, sectionName) {
    const trigger = triggerEl instanceof HTMLElement ? triggerEl : null;
    const container = trigger ? trigger.closest('[data-index-container]') : null;
    const sections = container
      ? [container.querySelector(`[data-section="${sectionName}"]`)].filter(Boolean)
      : Array.from(document.querySelectorAll(`[data-section="${sectionName}"]`));
    sections.forEach(section => {
      if (!section) return;
      const content = section.querySelector('.index-section-content');
      const arrow = section.querySelector('.section-arrow');
      const containerEl = section.closest('[data-index-container]');
      const key = `${this.getContainerKey(containerEl)}:${sectionName}`;
      if (this.collapsedSections.has(key)) {
        this.collapsedSections.delete(key);
        if (content) content.classList.remove('collapsed');
        if (arrow) arrow.textContent = '▼';
      } else {
        this.collapsedSections.add(key);
        if (content) content.classList.add('collapsed');
        if (arrow) arrow.textContent = '▶';
      }
    });
  }
}

