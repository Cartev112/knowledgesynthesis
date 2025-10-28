/**
 * Graph Viewer - Main coordinator for graph visualization
 * Extracted from main_ui.py
 */
import { state } from '../state.js';
import { API } from '../utils/api.js';
import { cytoscapeConfig, cytoscapeStyles, getLayoutConfig } from './cytoscape-config.js';
import { ModalManager } from './modals.js';
import { IndexPanelManager } from './index-panel.js';
import { VisualConfigManager } from './visual-config.js';

export class GraphViewer {
  constructor() {
    this.viewportMode = false;
    this.isLoading = false;
    this.loadedNodes = new Set();
    this.isOverEdge = false;
    this.isOverNode = false;
    this.isOverTooltip = false;
    this.hideTooltipTimeout = null;
    this.hideNodeTooltipTimeout = null;
    this.modalManager = new ModalManager();
    this.indexManager = new IndexPanelManager(this.modalManager);
    this.visualConfig = null; // Will be initialized after cy is created
    
    // Performance optimization: cache and debounce
    this.viewportCache = null;
    this.renderDebounceTimer = null;
    this.lastZoom = 1;
    this.lastPan = { x: 0, y: 0 };
  }

  async init() {
    console.log('Initializing Cytoscape graph viewer...');
    
    // Register dagre extension
    if (window.cytoscape && window.cytoscapeDagre) {
      window.cytoscape.use(window.cytoscapeDagre);
    }
    
    // Initialize Cytoscape
    state.cy = window.cytoscape({
      container: document.getElementById('cy'),
      elements: [],
      ...cytoscapeConfig,
      style: cytoscapeStyles
    });
    
    // Initialize visual configuration manager
    this.visualConfig = new VisualConfigManager(state.cy);
    
    // Wire up event handlers
    this.setupEventHandlers();
    
    console.log('Cytoscape initialized successfully');
  }

  applyVisualConfig() {
    if (this.visualConfig) {
      this.visualConfig.applyVisualConfig();
    }
  }

  applyLayout() {
    if (this.visualConfig) {
      this.visualConfig.applyLayout();
    }
  }

  resetVisualConfig() {
    if (this.visualConfig) {
      this.visualConfig.resetVisualConfig();
    }
  }
  
  setupEventHandlers() {
    const cy = state.cy;
    
    // Tooltip "Read More" button handler
    const readMoreBtn = document.getElementById('node-tooltip-read-more');
    if (readMoreBtn) {
      readMoreBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        // Get the currently hovered node data
        if (this.currentHoveredNode) {
          this.hideNodeTooltip();
          this.showNodeModal(this.currentHoveredNode);
        }
      });
    }
    const edgeReadMoreBtn = document.getElementById('tooltip-read-more');
    if (edgeReadMoreBtn) {
      edgeReadMoreBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (this.currentHoveredEdge) {
          this.hideEdgeTooltip();
          this.showEdgeModal(this.currentHoveredEdge.data());
        }
      });
    }
    
    // Node click handler with multi-select support
    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      const nodeId = node.id();
      const nodeLabel = node.data('label');
      
      if (evt.originalEvent && evt.originalEvent.shiftKey) {
        // Toggle multi-selection
        if (state.selectedNodes.has(nodeId)) {
          state.selectedNodes.delete(nodeId);
          node.removeClass('multi-selected');
        } else {
          state.selectedNodes.add(nodeId);
          node.addClass('multi-selected');
        }
        
        // Update FAB visibility
        this.updateFabVisibility();
        if (window.onSelectionChanged) {
          window.onSelectionChanged(Array.from(state.selectedNodes));
        }
      } else {
        // Regular click - show details
        this.showNodeModal(node.data());
      }
    });
    
    // Edge click handler with multi-select support
    cy.on('tap', 'edge', (evt) => {
      const edge = evt.target;
      const edgeId = edge.id();
      
      if (evt.originalEvent && evt.originalEvent.shiftKey) {
        // Toggle multi-selection for edges
        if (!state.selectedEdges) {
          state.selectedEdges = new Set();
        }
        
        if (state.selectedEdges.has(edgeId)) {
          state.selectedEdges.delete(edgeId);
          edge.removeClass('multi-selected');
        } else {
          state.selectedEdges.add(edgeId);
          edge.addClass('multi-selected');
        }
        
        // Notify selection changed
        if (window.onSelectionChanged) {
          window.onSelectionChanged(Array.from(state.selectedNodes), Array.from(state.selectedEdges));
        }
      } else {
        // Regular click - show details
        this.hideEdgeTooltip();
        this.showEdgeModal(edge.data());
      }
    });
    
    // Improved tooltip handlers with debouncing
    cy.on('mouseover', 'node', (evt) => {
      this.isOverNode = true;
      if (this.hideNodeTooltipTimeout) {
        clearTimeout(this.hideNodeTooltipTimeout);
      }
      if (this.showNodeTooltipTimeout) {
        clearTimeout(this.showNodeTooltipTimeout);
      }
      // Delay showing tooltip to avoid flicker on quick mouseovers
      this.showNodeTooltipTimeout = setTimeout(() => {
        this.showNodeTooltip(evt.target, evt);
      }, 150);
    });
    
    cy.on('mouseout', 'node', () => {
      this.isOverNode = false;
      if (this.showNodeTooltipTimeout) {
        clearTimeout(this.showNodeTooltipTimeout);
      }
      this.scheduleHideNodeTooltip();
    });
    
    cy.on('mouseover', 'edge', (evt) => {
      this.isOverEdge = true;
      if (this.hideTooltipTimeout) {
        clearTimeout(this.hideTooltipTimeout);
      }
      if (this.showEdgeTooltipTimeout) {
        clearTimeout(this.showEdgeTooltipTimeout);
      }
      // Delay showing tooltip to avoid flicker
      this.showEdgeTooltipTimeout = setTimeout(() => {
        this.showEdgeTooltip(evt.target, evt);
      }, 150);
    });
    
    cy.on('mouseout', 'edge', () => {
      this.isOverEdge = false;
      if (this.showEdgeTooltipTimeout) {
        clearTimeout(this.showEdgeTooltipTimeout);
      }
      this.scheduleHideTooltip();
    });
    
    // Background click
    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        this.clearAllHighlights();
      }
    });
  }
  
  async loadAllData() {
    try {
      // Fetch all pages to avoid missing newly ingested items due to pagination
      const pageSize = 1000;
      let page = 1;
      const nodesMap = new Map();
      const relsMap = new Map();
      
      while (true) {
        const data = await API.getAllGraph(pageSize, page);
        const nodes = data.nodes || [];
        const rels = data.relationships || [];
        nodes.forEach(n => nodesMap.set(n.id, n));
        rels.forEach(r => relsMap.set(r.id, r));
        if (nodes.length < pageSize) break;
        page++;
      }
      
      const allNodes = Array.from(nodesMap.values());
      const allRels = Array.from(relsMap.values());
      
      if (allNodes.length === 0 && allRels.length === 0) {
        alert('No data in the knowledge graph yet. Upload a document in the Ingestion tab to get started!');
        return;
      }
      
      if (allNodes.length > 200) {
        console.log('Large graph detected, enabling viewport-based loading');
        this.viewportMode = true;
      }
      
      this.renderGraph({ nodes: allNodes, relationships: allRels });
    } catch (e) {
      console.error('Failed to load all data:', e);
      alert('Failed to load graph data: ' + e.message);
    }
  }
  
  renderGraph(data) {
    const elements = [];
    const nodeIds = new Set();
    
    // First, add all nodes and track their IDs
    (data.nodes || []).forEach(n => {
      nodeIds.add(n.id);
      elements.push({
        data: {
          id: n.id,
          label: n.label || n.id,
          type: n.type,
          sources: n.sources,
          significance: n.significance
        }
      });
    });
    
    // Then add edges, but only if both source and target nodes exist
    let skippedEdges = 0;
    (data.relationships || []).forEach(r => {
      if (!nodeIds.has(r.source)) {
        console.warn(`Skipping edge ${r.id}: source node '${r.source}' not found`);
        skippedEdges++;
        return;
      }
      if (!nodeIds.has(r.target)) {
        console.warn(`Skipping edge ${r.id}: target node '${r.target}' not found`);
        skippedEdges++;
        return;
      }
      
      elements.push({
        data: {
          id: r.id,
          source: r.source,
          target: r.target,
          relation: r.relation,
          status: r.status || 'unverified',
          polarity: r.polarity || 'positive',
          confidence: r.confidence,
          significance: r.significance,
          sources: r.sources,
          page_number: r.page_number,
          original_text: r.original_text,
          reviewed_by_first_name: r.reviewed_by_first_name,
          reviewed_by_last_name: r.reviewed_by_last_name,
          reviewed_at: r.reviewed_at
        }
      });
    });
    
    if (skippedEdges > 0) {
      console.warn(`⚠️ Skipped ${skippedEdges} edges due to missing nodes. This indicates a data consistency issue in the backend.`);
    }
    
    state.cy.elements().remove();
    
    if (elements.length === 0) {
      return;
    }
    
    console.log(`Rendering ${nodeIds.size} nodes and ${elements.length - nodeIds.size} edges`);
    
    // Batch add elements for better performance
    state.cy.startBatch();
    state.cy.add(elements);
    state.cy.endBatch();
    
    // Apply layout
    const nodeCount = (data.nodes || []).length;
    const layoutConfig = getLayoutConfig(nodeCount);
    
    state.cy.resize();
    
    // Show loading indicator for large graphs
    if (nodeCount > 100) {
      console.log(`Laying out ${nodeCount} nodes...`);
    }
    
    const layout = state.cy.layout(layoutConfig);
    layout.run();
    
    layout.on('layoutstop', () => {
      // Use requestAnimationFrame for smoother fit
      requestAnimationFrame(() => {
        state.cy.fit(undefined, 30);
        // Populate index after graph is rendered
        this.indexManager.populateIndex();
      });
    });
  }
  
  showNodeTooltip(node, evt) {
    const tooltip = document.getElementById('node-tooltip');
    if (!tooltip) return;
    
    const data = node.data();
    // Store current node data for Read More button
    this.currentHoveredNode = data;
    
    document.getElementById('node-tooltip-label').textContent = data.label || data.id;
    document.getElementById('node-tooltip-type').textContent = `Type: ${data.type || 'N/A'}`;
    document.getElementById('node-tooltip-significance').textContent = data.significance ? `Significance: ${data.significance}/5` : '';
    
    // Smart positioning to keep tooltip on screen
    const x = evt.renderedPosition.x;
    const y = evt.renderedPosition.y;
    const offset = 15;
    
    // Position tooltip, ensuring it stays within viewport
    let left = x + offset;
    let top = y + offset;
    
    // Check if tooltip would go off right edge
    if (left + 300 > window.innerWidth) {
      left = x - 300 - offset;
    }
    
    // Check if tooltip would go off bottom edge
    if (top + 150 > window.innerHeight) {
      top = y - 150 - offset;
    }
    
    tooltip.style.left = Math.max(10, left) + 'px';
    tooltip.style.top = Math.max(10, top) + 'px';
    tooltip.classList.add('visible');
  }
  
  scheduleHideNodeTooltip() {
    if (this.hideNodeTooltipTimeout) {
      clearTimeout(this.hideNodeTooltipTimeout);
    }
    this.hideNodeTooltipTimeout = setTimeout(() => {
      if (!this.isOverNode) {
        this.hideNodeTooltip();
      }
    }, 200);
  }
  
  hideNodeTooltip() {
    const tooltip = document.getElementById('node-tooltip');
    if (tooltip) {
      tooltip.classList.remove('visible');
    }
  }
  
  showEdgeTooltip(edge, evt) {
    const tooltip = document.getElementById('edge-tooltip');
    if (!tooltip) return;
    
    const data = edge.data();
    this.currentHoveredEdge = edge;
    const sourceNode = state.cy.getElementById(data.source);
    const targetNode = state.cy.getElementById(data.target);
    
    document.getElementById('tooltip-source').textContent = sourceNode.data('label') || data.source;
    document.getElementById('tooltip-relation').textContent = data.relation;
    document.getElementById('tooltip-target').textContent = targetNode.data('label') || data.target;
    document.getElementById('tooltip-confidence').textContent = data.confidence ? `Confidence: ${(data.confidence * 100).toFixed(0)}%` : '';
    document.getElementById('tooltip-significance').textContent = data.significance ? `Significance: ${data.significance}/5` : '';
    
    // Smart positioning
    const x = evt.renderedPosition.x;
    const y = evt.renderedPosition.y;
    const offset = 15;
    
    let left = x + offset;
    let top = y + offset;
    
    // Keep tooltip on screen
    if (left + 300 > window.innerWidth) {
      left = x - 300 - offset;
    }
    if (top + 200 > window.innerHeight) {
      top = y - 200 - offset;
    }
    
    tooltip.style.left = Math.max(10, left) + 'px';
    tooltip.style.top = Math.max(10, top) + 'px';
    tooltip.classList.add('visible');
  }
  
  scheduleHideTooltip() {
    if (this.hideTooltipTimeout) {
      clearTimeout(this.hideTooltipTimeout);
    }
    this.hideTooltipTimeout = setTimeout(() => {
      if (!this.isOverEdge && !this.isOverTooltip) {
        this.hideEdgeTooltip();
      }
    }, 200);
  }
  
  hideEdgeTooltip() {
    const tooltip = document.getElementById('edge-tooltip');
    if (tooltip) {
      tooltip.classList.remove('visible');
    }
  }
  
  showNodeModal(data) {
    this.modalManager.showNodeModal(data);
  }
  
  showEdgeModal(data) {
    this.modalManager.showEdgeModal(data);
  }
  
  toggleIndex() {
    state.indexVisible = !state.indexVisible;
    const panel = document.getElementById('index-panel');
    const btn = document.getElementById('index-toggle-btn');
    
    if (panel) {
      if (state.indexVisible) {
        panel.classList.remove('hidden');
        if (btn) btn.classList.add('index-visible');
      } else {
        panel.classList.add('hidden');
        if (btn) btn.classList.remove('index-visible');
      }
    }
  }
  
  toggleLegend() {
    const modal = document.getElementById('legend-modal-overlay');
    if (modal) {
      modal.classList.toggle('visible');
    }
  }
  
  updateFabVisibility() {
    const fabContainer = document.getElementById('fab-container-2node');
    if (!fabContainer) return;
    
    // Show FAB only when exactly 2 nodes are selected
    if (state.selectedNodes.size === 2) {
      fabContainer.classList.remove('hidden');
    } else {
      fabContainer.classList.add('hidden');
    }
  }
  
  clearSelection() {
    state.selectedNodes.clear();
    if (state.selectedEdges) {
      state.selectedEdges.clear();
    }
    if (state.cy) {
      state.cy.nodes().removeClass('multi-selected');
      state.cy.edges().removeClass('multi-selected');
    }
    this.updateFabVisibility();
    if (window.onSelectionChanged) {
      window.onSelectionChanged([]);
    }
  }
  
  clearAllHighlights() {
    if (state.cy) {
      state.cy.nodes().removeClass('highlighted neighbor');
    }
  }
  
  focusNode(nodeId) {
    if (!state.cy) return;
    
    const node = state.cy.getElementById(nodeId);
    if (node.length > 0) {
      // Clear existing highlights
      this.clearAllHighlights();
      
      // Highlight the node
      node.addClass('highlighted');
      
      // Zoom to the node
      state.cy.animate({
        center: { eles: node },
        zoom: 1.5
      }, {
        duration: 500
      });
      
      // Close document modal
      const modal = document.getElementById('document-modal-overlay');
      if (modal) modal.classList.remove('visible');
    }
  }
  
  focusRelationship(edgeId) {
    if (!state.cy) return;
    
    let edge = state.cy.getElementById(edgeId);
    
    // If not found by ID, try to find by source-target pattern
    if (edge.length === 0 && edgeId.includes('-')) {
      const [sourceId, targetId] = edgeId.split('-');
      edge = state.cy.edges().filter(e => {
        return e.data('source') === sourceId && e.data('target') === targetId;
      }).first();
    }
    
    if (edge.length > 0) {
      // Clear existing highlights
      this.clearAllHighlights();
      
      // Highlight source and target nodes
      const source = edge.source();
      const target = edge.target();
      source.addClass('highlighted');
      target.addClass('highlighted');
      
      // Zoom to show both nodes
      state.cy.animate({
        fit: { eles: edge.union(source).union(target), padding: 100 }
      }, {
        duration: 500
      });
      
      // Show edge details after animation
      setTimeout(() => {
        this.showEdgeModal(edge.data());
      }, 600);
      
      // Close document modal
      const modal = document.getElementById('document-modal-overlay');
      if (modal) modal.classList.remove('visible');
    } else {
      console.warn('Could not find edge with ID:', edgeId);
    }
  }
}
