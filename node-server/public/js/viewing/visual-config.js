/**
 * Visual Configuration Manager
 * Handles visual customization of the graph (colors, sizes, layouts)
 */
import { state } from '../state.js';
import { cytoscapeStyles } from './cytoscape-config.js';

const LEGEND_PAGE_SIZE = 8;

const STATIC_NODE_LEGEND = [
  { selector: 'node', label: 'Default Node', prop: 'background-color' },
  { selector: 'node.highlighted', label: 'Search Highlight', prop: 'background-color' },
  { selector: 'node.neighbor', label: 'Neighbor Highlight', prop: 'background-color' },
  { selector: 'node.multi-selected', label: 'Multi-selected Node', prop: 'background-color' },
  { selector: 'node.manual-selected', label: 'Manual Selection', prop: 'background-color', note: 'Dashed border' },
  { selector: 'node:selected', label: 'Active Selection', prop: 'background-color' }
];

const STATIC_EDGE_LEGEND = [
  { selector: 'edge', label: 'Default Edge', prop: 'line-color' },
  { selector: 'edge[status = \"verified\"]', label: 'Verified Edge', prop: 'line-color' },
  { selector: 'edge[status = \"incorrect\"]', label: 'Incorrect Edge', prop: 'line-color', note: 'Dashed line' },
  { selector: 'edge.multi-selected', label: 'Multi-selected Edge', prop: 'line-color' },
  { selector: 'edge:selected', label: 'Active Selection', prop: 'line-color' }
];

export class VisualConfigManager {
  constructor(cy) {
    this.cy = cy;
    this.config = {
      nodeColorScheme: 'default',
      nodeSizeScheme: 'by-significance',
      edgeStyleScheme: 'default',
      labelDisplayScheme: 'hover',
      layoutAlgorithm: 'cose'
    };
    
    // Color palettes
    this.colorPalettes = {
      categorical: [
        '#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444',
        '#ec4899', '#14b8a6', '#f97316', '#06b6d4', '#84cc16'
      ],
      sequential: [
        '#ede9fe', '#ddd6fe', '#c4b5fd', '#a78bfa', '#8b5cf6',
        '#7c3aed', '#6d28d9', '#5b21b6', '#4c1d95'
      ]
    };

    this.legendConfig = {
      node: { entries: [], page: 0, pageSize: LEGEND_PAGE_SIZE },
      edge: { entries: [], page: 0, pageSize: LEGEND_PAGE_SIZE }
    };
    this.legendInitialized = false;
    this.tabButtons = [];
    this.tabContents = [];
    this.defaultNodeColor = this.getStyleColor('node', 'background-color', '#8b5cf6');
    this.defaultEdgeColor = this.getStyleColor('edge', 'line-color', '#9ca3af');
    this.noDocumentNodeColor = '#9ca3af';

    this.setupLegendUI();
  }

  ensureLegendLayout() {
    const modal = document.getElementById('legend-modal');
    const modalBody = modal?.querySelector('.modal-body');
    if (!modalBody || modalBody.querySelector('.visual-config-tab-bar')) {
      return;
    }

    const configGrid = modalBody.querySelector('.config-grid');
    const configActions = modalBody.querySelector('.config-actions');
    const colorLegend = configGrid?.querySelector('#color-legend');
    const edgeLegend = configGrid?.querySelector('#edge-legend');

    if (!configGrid || !configActions || !colorLegend || !edgeLegend) {
      return;
    }

    colorLegend.classList.remove('visible');
    edgeLegend.classList.remove('visible');

    const tabBar = document.createElement('div');
    tabBar.className = 'visual-config-tab-bar';

    const configTab = document.createElement('button');
    configTab.type = 'button';
    configTab.className = 'visual-config-tab active';
    configTab.setAttribute('data-visual-config-tab', 'config');
    configTab.textContent = 'Configuration';

    const legendTab = document.createElement('button');
    legendTab.type = 'button';
    legendTab.className = 'visual-config-tab';
    legendTab.setAttribute('data-visual-config-tab', 'legend');
    legendTab.textContent = 'Legend';

    tabBar.appendChild(configTab);
    tabBar.appendChild(legendTab);

    const configContent = document.createElement('div');
    configContent.className = 'visual-config-tab-content active';
    configContent.setAttribute('data-visual-config-content', 'config');
    configContent.appendChild(configGrid);
    configContent.appendChild(configActions);

    const legendContent = document.createElement('div');
    legendContent.className = 'visual-config-tab-content';
    legendContent.setAttribute('data-visual-config-content', 'legend');

    const legendSections = document.createElement('div');
    legendSections.className = 'legend-sections';

    const staticNodeLegend = document.createElement('div');
    staticNodeLegend.id = 'static-node-legend';
    staticNodeLegend.className = 'color-legend-container';

    const nodeStylesSection = this.buildLegendSection('Node Styles', staticNodeLegend);

    const nodePagination = document.createElement('div');
    nodePagination.id = 'color-legend-pagination';
    nodePagination.className = 'legend-pagination';
    const nodeMappingSection = this.buildLegendSection('Node Color Mapping', colorLegend, nodePagination);

    const staticEdgeLegend = document.createElement('div');
    staticEdgeLegend.id = 'static-edge-legend';
    staticEdgeLegend.className = 'color-legend-container';

    const edgeStylesSection = this.buildLegendSection('Edge Styles', staticEdgeLegend);

    const edgePagination = document.createElement('div');
    edgePagination.id = 'edge-legend-pagination';
    edgePagination.className = 'legend-pagination';
    const edgeMappingSection = this.buildLegendSection('Edge Color Mapping', edgeLegend, edgePagination);

    legendSections.appendChild(nodeStylesSection);
    legendSections.appendChild(nodeMappingSection);
    legendSections.appendChild(edgeStylesSection);
    legendSections.appendChild(edgeMappingSection);

    legendContent.appendChild(legendSections);

    modalBody.innerHTML = '';
    modalBody.appendChild(tabBar);
    modalBody.appendChild(configContent);
    modalBody.appendChild(legendContent);
  }

  buildLegendSection(title, contentElement, paginationElement) {
    const section = document.createElement('div');
    section.className = 'legend-section';

    if (title || paginationElement) {
      const header = document.createElement('div');
      header.className = 'legend-section-header';

      if (title) {
        const heading = document.createElement('h3');
        heading.className = 'legend-section-title';
        heading.textContent = title;
        header.appendChild(heading);
      }

      if (paginationElement) {
        paginationElement.classList.remove('visible');
        header.appendChild(paginationElement);
      }

      section.appendChild(header);
    }

    section.appendChild(contentElement);
    return section;
  }

  setupLegendUI() {
    this.ensureLegendLayout();
    if (this.legendInitialized) return;

    const tabButtons = document.querySelectorAll('[data-visual-config-tab]');
    const tabContents = document.querySelectorAll('[data-visual-config-content]');

    if (!tabButtons.length || !tabContents.length) {
      return;
    }

    this.legendInitialized = true;
    this.tabButtons = Array.from(tabButtons);
    this.tabContents = Array.from(tabContents);

    this.tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        const targetTab = button.getAttribute('data-visual-config-tab') || 'config';
        this.switchLegendTab(targetTab);
      });
    });

    this.switchLegendTab('config');
    this.renderStaticLegends();
  }

  switchLegendTab(tabName) {
    if (!this.tabButtons.length || !this.tabContents.length) return;

    this.tabButtons.forEach(button => {
      const isActive = button.getAttribute('data-visual-config-tab') === tabName;
      button.classList.toggle('active', isActive);
    });

    this.tabContents.forEach(content => {
      const isActive = content.getAttribute('data-visual-config-content') === tabName;
      content.classList.toggle('active', isActive);
    });
  }

  getStyleColor(selector, property, fallback) {
    const entry = cytoscapeStyles.find(style => style.selector === selector);
    if (entry && entry.style) {
      const value = entry.style[property];
      if (typeof value === 'string' && value.trim().length > 0) {
        return value;
      }
    }
    return fallback;
  }

  renderStaticLegends() {
    const nodeContainer = document.getElementById('static-node-legend');
    const edgeContainer = document.getElementById('static-edge-legend');

    if (nodeContainer) {
      const nodeEntries = this.buildStaticLegendEntries(STATIC_NODE_LEGEND);
      this.setLegendContainer(nodeContainer, nodeEntries, {
        showWhenEmpty: true,
        emptyMessage: 'No node styles available.'
      });
    }

    if (edgeContainer) {
      const edgeEntries = this.buildStaticLegendEntries(STATIC_EDGE_LEGEND);
      this.setLegendContainer(edgeContainer, edgeEntries, {
        showWhenEmpty: true,
        emptyMessage: 'No edge styles available.'
      });
    }
  }

  buildStaticLegendEntries(configList) {
    return configList.map(item => {
      const styleEntry = cytoscapeStyles.find(entry => entry.selector === item.selector);
      if (!styleEntry || !styleEntry.style) return null;

      const rawValue = styleEntry.style[item.prop];
      if (typeof rawValue === 'function') return null;

      const color = rawValue;
      if (!color) return null;

      return {
        label: item.label,
        color,
        note: item.note || ''
      };
    }).filter(Boolean);
  }

  setLegendContainer(container, entries, options = {}) {
    const { showWhenEmpty = false, emptyMessage = 'No legend data available.' } = options;

    if (!container) return;

    if (!entries || entries.length === 0) {
      container.innerHTML = showWhenEmpty ? `
        <div class="legend-empty">${this.escapeHtml(emptyMessage)}</div>
      ` : '';
      container.classList.toggle('visible', showWhenEmpty);
      return;
    }

    container.innerHTML = this.buildLegendItemsHtml(entries);
    container.classList.add('visible');
  }

  buildLegendItemsHtml(entries) {
    return entries.map(item => `
      <div class="color-legend-item">
        <div class="color-legend-swatch" style="background-color: ${item.color}"></div>
        <div class="color-legend-text">
          <span class="color-legend-label">${this.escapeHtml(item.label)}</span>
          ${item.note ? `<span class="legend-note">${this.escapeHtml(item.note)}</span>` : ''}
        </div>
      </div>
    `).join('');
  }

  updateLegendData(type, legendData) {
    this.setupLegendUI();
    const legendState = this.legendConfig[type];
    if (!legendState) return;

    const entries = Object.entries(legendData || {}).map(([label, color]) => ({
      label,
      color,
      note: ''
    }));

    legendState.entries = entries;
    legendState.page = 0;

    this.renderPaginatedLegend(type);
  }

  renderPaginatedLegend(type) {
    const state = this.legendConfig[type];
    if (!state) return;

    const containerId = type === 'node' ? 'color-legend' : 'edge-legend';
    const paginationId = type === 'node' ? 'color-legend-pagination' : 'edge-legend-pagination';

    const container = document.getElementById(containerId);
    const pagination = document.getElementById(paginationId);

    if (!container || !pagination) return;

    const entries = state.entries || [];

    if (!entries.length) {
      this.setLegendContainer(container, [], {
        showWhenEmpty: true,
        emptyMessage: 'Select a color scheme to view legend details.'
      });
      pagination.innerHTML = '';
      pagination.classList.remove('visible');
      return;
    }

    const totalPages = Math.ceil(entries.length / state.pageSize);
    if (state.page >= totalPages) {
      state.page = totalPages - 1;
    }

    const start = state.page * state.pageSize;
    const pageEntries = entries.slice(start, start + state.pageSize);

    this.setLegendContainer(container, pageEntries);
    this.renderPaginationControls(type, pagination, totalPages, state.page);
  }

  renderPaginationControls(type, container, totalPages, currentPage) {
    container.innerHTML = '';

    if (totalPages <= 1) {
      container.classList.remove('visible');
      return;
    }

    container.classList.add('visible');

    const prevButton = this.createPaginationButton('Previous', currentPage === 0, () => {
      this.changeLegendPage(type, currentPage - 1);
    });

    const indicator = document.createElement('span');
    indicator.className = 'legend-page-indicator';
    indicator.textContent = `Page ${currentPage + 1} of ${totalPages}`;

    const nextButton = this.createPaginationButton('Next', currentPage >= totalPages - 1, () => {
      this.changeLegendPage(type, currentPage + 1);
    });

    container.appendChild(prevButton);
    container.appendChild(indicator);
    container.appendChild(nextButton);
  }

  createPaginationButton(label, disabled, handler) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'legend-page-btn';
    button.textContent = label;
    button.disabled = disabled;

    if (!disabled) {
      button.addEventListener('click', handler);
    }

    return button;
  }

  changeLegendPage(type, newPage) {
    const state = this.legendConfig[type];
    if (!state) return;

    const totalPages = Math.ceil((state.entries || []).length / state.pageSize);
    if (totalPages === 0) return;

    const clampedPage = Math.max(0, Math.min(newPage, totalPages - 1));
    state.page = clampedPage;
    this.renderPaginatedLegend(type);
  }

  clearLegend(type, message = '') {
    this.setupLegendUI();
    const containerId = type === 'node' ? 'color-legend' : 'edge-legend';
    const paginationId = type === 'node' ? 'color-legend-pagination' : 'edge-legend-pagination';

    const container = document.getElementById(containerId);
    const pagination = document.getElementById(paginationId);

    const legendState = this.legendConfig[type];
    if (legendState) {
      legendState.entries = [];
      legendState.page = 0;
    }

    if (container) {
      if (message) {
        this.setLegendContainer(container, [], {
          showWhenEmpty: true,
          emptyMessage: message
        });
      } else {
        container.innerHTML = '';
        container.classList.remove('visible');
      }
    }

    if (pagination) {
      pagination.innerHTML = '';
      pagination.classList.remove('visible');
    }
  }

  applyVisualConfig() {
    if (!this.cy) return;
    this.setupLegendUI();

    // Read current config from UI
    this.config.nodeColorScheme = document.getElementById('node-color-scheme')?.value || 'default';
    this.config.nodeSizeScheme = document.getElementById('node-size-scheme')?.value || 'uniform';
    this.config.edgeStyleScheme = document.getElementById('edge-style-scheme')?.value || 'default';
    this.config.labelDisplayScheme = document.getElementById('label-display-scheme')?.value || 'hover';

    // Apply configurations
    this.applyNodeColors();
    this.applyNodeSizes();
    this.applyEdgeStyles();
    this.applyLabelDisplay();
  }

  applyNodeColors() {
    this.setupLegendUI();
    const scheme = this.config.nodeColorScheme;
    
    switch (scheme) {
      case 'by-type':
        this.colorNodesByType();
        this.showColorLegend(this.getTypeLegend());
        break;
      case 'by-user':
        this.colorNodesByUser();
        this.showColorLegend(this.getUserLegend());
        break;
      case 'by-document':
        this.colorNodesByDocument();
        this.showColorLegend(this.getDocumentLegend());
        break;
      case 'by-degree':
        this.colorNodesByDegree();
        this.showColorLegend(this.getDegreeLegend());
        break;
      default:
        this.colorNodesDefault();
        this.clearLegend('node', 'Default scheme uses the base node style.');
    }
  }

  colorNodesDefault() {
    this.cy.nodes().style('background-color', this.defaultNodeColor);
  }

  colorNodesByType() {
    const types = new Set();
    this.cy.nodes().forEach(n => types.add(n.data('type') || 'Entity'));
    
    const typeArray = Array.from(types);
    const colorMap = {};
    typeArray.forEach((type, i) => {
      colorMap[type] = this.colorPalettes.categorical[i % this.colorPalettes.categorical.length];
    });

    this.cy.nodes().forEach(node => {
      const type = node.data('type') || 'Entity';
      node.style('background-color', colorMap[type]);
    });

    return colorMap;
  }

  colorNodesByUser() {
    const users = new Set();
    this.cy.nodes().forEach(n => {
      const creator = n.data('created_by') || n.data('user') || 'Unknown';
      users.add(creator);
    });
    
    const userArray = Array.from(users);
    const colorMap = {};
    userArray.forEach((user, i) => {
      colorMap[user] = this.colorPalettes.categorical[i % this.colorPalettes.categorical.length];
    });

    this.cy.nodes().forEach(node => {
      const creator = node.data('created_by') || node.data('user') || 'Unknown';
      node.style('background-color', colorMap[creator]);
    });

    return colorMap;
  }

  colorNodesByDocument() {
    const docs = new Set();
    const docLabels = new Map();

    this.cy.nodes().forEach(n => {
      const sources = n.data('sources') || [];
      sources.forEach(source => {
        const info = this.normalizeDocumentSource(source);
        if (info && info.id) {
          docs.add(info.id);
          if (!docLabels.has(info.id)) {
            docLabels.set(info.id, info.label);
          }
        }
      });
    });
    
    const docArray = Array.from(docs);
    const colorMap = {};
    docArray.forEach((docId, i) => {
      colorMap[docId] = this.colorPalettes.categorical[i % this.colorPalettes.categorical.length];
    });

    let hasUnattributedNodes = false;
    this.cy.nodes().forEach(node => {
      const sources = node.data('sources') || [];
      if (sources.length > 0) {
        const info = this.normalizeDocumentSource(sources[0]);
        if (info && info.id && colorMap[info.id]) {
          node.style('background-color', colorMap[info.id]);
        } else {
          node.style('background-color', this.defaultNodeColor);
        }
      } else {
        node.style('background-color', this.noDocumentNodeColor);
        hasUnattributedNodes = true;
      }
    });

    const legend = {};
    docArray.forEach(docId => {
      const baseLabel = docLabels.get(docId) || this.getDocumentTitleById(docId);
      const label = this.createUniqueLegendLabel(legend, baseLabel, docId);
      legend[label] = colorMap[docId];
    });

    if (hasUnattributedNodes) {
      legend['No Document Source'] = this.noDocumentNodeColor;
    }

    return legend;
  }

  colorNodesByDegree() {
    const degrees = this.cy.nodes().map(n => n.degree());
    const maxDegree = Math.max(...degrees);
    const minDegree = Math.min(...degrees);

    this.cy.nodes().forEach(node => {
      const degree = node.degree();
      const normalized = maxDegree === minDegree ? 0.5 : (degree - minDegree) / (maxDegree - minDegree);
      const colorIndex = Math.floor(normalized * (this.colorPalettes.sequential.length - 1));
      node.style('background-color', this.colorPalettes.sequential[colorIndex]);
    });
  }

  applyNodeSizes() {
    const scheme = this.config.nodeSizeScheme;
    
    switch (scheme) {
      case 'by-significance':
        this.sizeNodesBySignificance();
        break;
      case 'by-degree':
        this.sizeNodesByDegree();
        break;
      case 'by-importance':
        this.sizeNodesByImportance();
        break;
      case 'uniform':
        this.sizeNodesUniform();
        break;
      default:
        this.sizeNodesBySignificance();
    }
  }

  sizeNodesBySignificance() {
    this.cy.nodes().forEach(node => {
      const significance = node.data('significance') || 3; // Default to 3 if not set
      // Map significance (1-5) to size (20-60px)
      // 1 -> 20px, 2 -> 30px, 3 -> 40px, 4 -> 50px, 5 -> 60px
      const size = 10 + (significance * 10);
      node.style('width', size);
      node.style('height', size);
    });
  }

  sizeNodesUniform() {
    this.cy.nodes().style('width', 30);
    this.cy.nodes().style('height', 30);
  }

  sizeNodesByDegree() {
    const degrees = this.cy.nodes().map(n => n.degree());
    const maxDegree = Math.max(...degrees);
    const minDegree = Math.min(...degrees);

    this.cy.nodes().forEach(node => {
      const degree = node.degree();
      const normalized = maxDegree === minDegree ? 0.5 : (degree - minDegree) / (maxDegree - minDegree);
      const size = 20 + (normalized * 40); // 20-60px range
      node.style('width', size);
      node.style('height', size);
    });
  }

  sizeNodesByImportance() {
    // Use betweenness centrality as a measure of importance
    const bc = this.cy.elements().betweennessCentrality();
    const centralities = this.cy.nodes().map(n => bc.betweenness(n));
    const maxCent = Math.max(...centralities);
    const minCent = Math.min(...centralities);

    this.cy.nodes().forEach(node => {
      const cent = bc.betweenness(node);
      const normalized = maxCent === minCent ? 0.5 : (cent - minCent) / (maxCent - minCent);
      const size = 20 + (normalized * 40);
      node.style('width', size);
      node.style('height', size);
    });
  }

  applyEdgeStyles() {
    this.setupLegendUI();
    const scheme = this.config.edgeStyleScheme;
    
    switch (scheme) {
      case 'by-type':
        this.colorEdgesByType();
        this.showEdgeLegend(this.getEdgeTypeLegend());
        break;
      case 'by-document':
        this.colorEdgesByDocument();
        this.showEdgeLegend(this.getEdgeDocumentLegend());
        break;
      default:
        this.colorEdgesDefault();
        this.clearLegend('edge', 'Default scheme uses the base edge style.');
    }
  }

  colorEdgesDefault() {
    this.cy.edges().style({
      'line-color': this.defaultEdgeColor,
      'target-arrow-color': this.defaultEdgeColor
    });
  }

  colorEdgesByType() {
    const types = new Set();
    this.cy.edges().forEach(e => types.add(e.data('relation') || 'relates to'));
    
    const typeArray = Array.from(types);
    const colorMap = {};
    typeArray.forEach((type, i) => {
      colorMap[type] = this.colorPalettes.categorical[i % this.colorPalettes.categorical.length];
    });

    this.cy.edges().forEach(edge => {
      const type = edge.data('relation') || 'relates to';
      edge.style('line-color', colorMap[type]);
      edge.style('target-arrow-color', colorMap[type]);
    });

    return colorMap;
  }

  colorEdgesByDocument() {
    const docs = new Set();
    const docLabels = new Map();
    this.cy.edges().forEach(e => {
      const sources = e.data('sources') || [];
      sources.forEach(source => {
        const info = this.normalizeDocumentSource(source);
        if (info && info.id) {
          docs.add(info.id);
          if (!docLabels.has(info.id)) {
            docLabels.set(info.id, info.label);
          }
        }
      });
    });
    
    const docArray = Array.from(docs);
    const colorMap = {};
    docArray.forEach((doc, i) => {
      colorMap[doc] = this.colorPalettes.categorical[i % this.colorPalettes.categorical.length];
    });

    let hasUnattributedEdges = false;
    this.cy.edges().forEach(edge => {
      const sources = edge.data('sources') || [];
      if (sources.length > 0) {
        const info = this.normalizeDocumentSource(sources[0]);
        if (info && info.id && colorMap[info.id]) {
          edge.style('line-color', colorMap[info.id]);
          edge.style('target-arrow-color', colorMap[info.id]);
        } else {
          edge.style('line-color', this.defaultEdgeColor);
          edge.style('target-arrow-color', this.defaultEdgeColor);
        }
      } else {
        edge.style('line-color', this.defaultEdgeColor);
        edge.style('target-arrow-color', this.defaultEdgeColor);
        hasUnattributedEdges = true;
      }
    });

    const legend = {};
    docArray.forEach(docId => {
      const baseLabel = docLabels.get(docId) || this.getDocumentTitleById(docId);
      const label = this.createUniqueLegendLabel(legend, baseLabel, docId);
      legend[label] = colorMap[docId];
    });

    if (hasUnattributedEdges) {
      legend['No Document Source'] = this.defaultEdgeColor;
    }

    return legend;
  }

  applyLabelDisplay() {
    const scheme = this.config.labelDisplayScheme;
    
    switch (scheme) {
      case 'always':
        this.cy.nodes().style('label', ele => ele.data('label'));
        break;
      case 'selected':
        this.cy.nodes().style('label', '');
        this.cy.nodes('.multi-selected').style('label', ele => ele.data('label'));
        break;
      case 'never':
        this.cy.nodes().style('label', '');
        break;
      default: // hover
        this.cy.nodes().style('label', '');
    }
  }

  applyLayout() {
    const algorithm = document.getElementById('layout-algorithm')?.value || 'cose';
    this.config.layoutAlgorithm = algorithm;

    const layoutOptions = this.getLayoutOptions(algorithm);
    const layout = this.cy.layout(layoutOptions);
    layout.run();
  }

  getLayoutOptions(algorithm) {
    const baseOptions = {
      name: algorithm,
      animate: true,
      animationDuration: 500,
      fit: true,
      padding: 50
    };

    switch (algorithm) {
      case 'cose':
        return { ...baseOptions, nodeRepulsion: 8000, idealEdgeLength: 100 };
      case 'fcose':
        return { ...baseOptions, quality: 'default', randomize: false };
      case 'cola':
        return { ...baseOptions, edgeLength: 100, nodeSpacing: 50 };
      case 'circle':
        return { ...baseOptions, radius: 300 };
      case 'grid':
        return { ...baseOptions, rows: undefined, cols: undefined };
      case 'concentric':
        return { ...baseOptions, concentric: n => n.degree(), levelWidth: () => 2 };
      case 'breadthfirst':
        return { ...baseOptions, directed: true, spacingFactor: 1.5 };
      default:
        return baseOptions;
    }
  }

  showColorLegend(legendData) {
    if (!legendData || Object.keys(legendData).length === 0) {
      this.clearLegend('node');
      return;
    }

    this.updateLegendData('node', legendData);
  }

  showEdgeLegend(legendData) {
    if (!legendData || Object.keys(legendData).length === 0) {
      this.clearLegend('edge');
      return;
    }

    this.updateLegendData('edge', legendData);
  }

  getTypeLegend() {
    return this.colorNodesByType();
  }

  getUserLegend() {
    return this.colorNodesByUser();
  }

  getDocumentLegend() {
    return this.colorNodesByDocument();
  }

  getDegreeLegend() {
    return {
      'Low (0-2)': this.colorPalettes.sequential[0],
      'Medium (3-5)': this.colorPalettes.sequential[4],
      'High (6+)': this.colorPalettes.sequential[8]
    };
  }

  getEdgeTypeLegend() {
    return this.colorEdgesByType();
  }

  getEdgeDocumentLegend() {
    return this.colorEdgesByDocument();
  }

  normalizeDocumentSource(source) {
    if (!source) return null;

    if (typeof source === 'object') {
      const rawId = source.id ?? source.document_id ?? source.uuid ?? source._id ?? source.slug ?? source.identifier ?? null;
      const id = rawId != null ? String(rawId) : null;
      const labelCandidates = [
        source.title,
        source.name,
        source.displayName,
        source.filename,
        source.label
      ];
      const candidateLabel = labelCandidates.find(val => typeof val === 'string' && val.trim().length > 0);
      const label = candidateLabel || (id ? this.getDocumentTitleById(id) : '');
      const finalLabel = label || 'Untitled Document';
      const finalId = id || `doc:${finalLabel}`;
      return { id: finalId, label: finalLabel };
    }

    const id = String(source);
    return {
      id,
      label: this.getDocumentTitleById(id)
    };
  }

  getDocumentTitleById(docId) {
    if (docId === undefined || docId === null) {
      return 'Unknown Document';
    }

    const normalizedId = String(docId);
    const docs = Array.isArray(state.documents) ? state.documents : [];

    for (const doc of docs) {
      if (!doc) continue;
      const candidateIds = [
        doc.id,
        doc.document_id,
        doc.uuid,
        doc._id,
        doc.external_id
      ];

      const matches = candidateIds.some(candidate => {
        if (candidate === undefined || candidate === null) return false;
        return String(candidate) === normalizedId;
      });

      if (matches) {
        const titleCandidates = [
          doc.title,
          doc.name,
          doc.displayName,
          doc.filename,
          doc.metadata?.title
        ];

        const title = titleCandidates.find(value => typeof value === 'string' && value.trim().length > 0);
        return title || normalizedId;
      }
    }

    return normalizedId;
  }

  createUniqueLegendLabel(legend, baseLabel, identifier) {
    if (!legend || !legend[baseLabel]) return baseLabel;

    const normalizedId = identifier ? String(identifier).slice(0, 8) : '';
    let attempt = 1;
    let candidate = normalizedId
      ? `${baseLabel} (${normalizedId})`
      : `${baseLabel} (${attempt})`;

    while (legend[candidate]) {
      attempt += 1;
      candidate = normalizedId
        ? `${baseLabel} (${normalizedId}-${attempt})`
        : `${baseLabel} (${attempt})`;
    }

    return candidate;
  }

  resetVisualConfig() {
    // Reset UI controls
    document.getElementById('node-color-scheme').value = 'default';
    document.getElementById('node-size-scheme').value = 'by-significance';
    document.getElementById('edge-style-scheme').value = 'default';
    document.getElementById('label-display-scheme').value = 'hover';
    document.getElementById('layout-algorithm').value = 'cose';

    // Reset config
    this.config = {
      nodeColorScheme: 'default',
      nodeSizeScheme: 'by-significance',
      edgeStyleScheme: 'default',
      labelDisplayScheme: 'hover',
      layoutAlgorithm: 'cose'
    };

    // Apply defaults
    this.applyVisualConfig();
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}
