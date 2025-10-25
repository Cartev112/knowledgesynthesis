/**
 * Visual Configuration Manager
 * Handles visual customization of the graph (colors, sizes, layouts)
 */
import { state } from '../state.js';

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
  }

  applyVisualConfig() {
    if (!this.cy) return;

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
    const scheme = this.config.nodeColorScheme;
    const colorLegend = document.getElementById('color-legend');
    
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
        if (colorLegend) colorLegend.classList.remove('visible');
    }
  }

  colorNodesDefault() {
    this.cy.nodes().style('background-color', '#8b5cf6');
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
    this.cy.nodes().forEach(n => {
      const sources = n.data('sources') || [];
      sources.forEach(s => {
        const docId = typeof s === 'object' ? s.id : s;
        docs.add(docId);
      });
    });
    
    const docArray = Array.from(docs);
    const colorMap = {};
    docArray.forEach((doc, i) => {
      colorMap[doc] = this.colorPalettes.categorical[i % this.colorPalettes.categorical.length];
    });

    this.cy.nodes().forEach(node => {
      const sources = node.data('sources') || [];
      if (sources.length > 0) {
        const firstDoc = typeof sources[0] === 'object' ? sources[0].id : sources[0];
        node.style('background-color', colorMap[firstDoc] || '#8b5cf6');
      } else {
        node.style('background-color', '#9ca3af');
      }
    });

    return colorMap;
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
    const scheme = this.config.edgeStyleScheme;
    const edgeLegend = document.getElementById('edge-legend');
    
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
        if (edgeLegend) edgeLegend.classList.remove('visible');
    }
  }

  colorEdgesDefault() {
    this.cy.edges().style('line-color', '#9ca3af');
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
    });

    return colorMap;
  }

  colorEdgesByDocument() {
    const docs = new Set();
    this.cy.edges().forEach(e => {
      const sources = e.data('sources') || [];
      sources.forEach(s => {
        const docId = typeof s === 'object' ? s.id : s;
        docs.add(docId);
      });
    });
    
    const docArray = Array.from(docs);
    const colorMap = {};
    docArray.forEach((doc, i) => {
      colorMap[doc] = this.colorPalettes.categorical[i % this.colorPalettes.categorical.length];
    });

    this.cy.edges().forEach(edge => {
      const sources = edge.data('sources') || [];
      if (sources.length > 0) {
        const firstDoc = typeof sources[0] === 'object' ? sources[0].id : sources[0];
        edge.style('line-color', colorMap[firstDoc] || '#9ca3af');
      } else {
        edge.style('line-color', '#9ca3af');
      }
    });

    return colorMap;
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
    const container = document.getElementById('color-legend');
    if (!container || !legendData) return;

    container.innerHTML = Object.entries(legendData).map(([key, color]) => `
      <div class="color-legend-item">
        <div class="color-legend-swatch" style="background-color: ${color}"></div>
        <span class="color-legend-label">${this.escapeHtml(key)}</span>
      </div>
    `).join('');
    
    container.classList.add('visible');
  }

  showEdgeLegend(legendData) {
    const container = document.getElementById('edge-legend');
    if (!container || !legendData) return;

    container.innerHTML = Object.entries(legendData).map(([key, color]) => `
      <div class="color-legend-item">
        <div class="color-legend-swatch" style="background-color: ${color}"></div>
        <span class="color-legend-label">${this.escapeHtml(key)}</span>
      </div>
    `).join('');
    
    container.classList.add('visible');
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
