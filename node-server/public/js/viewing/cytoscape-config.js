/**
 * Cytoscape Configuration and Styles
 */

export const cytoscapeConfig = {
  wheelSensitivity: 0.2,
  minZoom: 0.1,
  maxZoom: 3,
  // Performance optimizations
  textureOnViewport: true, // Use texture during viewport changes
  motionBlur: true, // Enable motion blur for smoother feel
  motionBlurOpacity: 0.2,
  hideEdgesOnViewport: false, // Keep edges visible for better UX
  hideLabelsOnViewport: false, // Keep labels visible for better UX
  pixelRatio: 'auto',
  // Additional performance settings
  boxSelectionEnabled: false,
  selectionType: 'single',
  autoungrabify: false,
  autounselectify: false
};

export const cytoscapeStyles = [
  {
    selector: 'node',
    style: {
      'label': 'data(label)',
      'font-size': '12px',
      'text-wrap': 'wrap',
      'text-max-width': 150,
      'text-halign': 'center',
      'text-valign': 'center',
      'background-color': '#667eea',
      'color': '#ffffff',
      'text-outline-color': '#667eea',
      'text-outline-width': 2,
      'width': function(ele) {
        const sig = ele.data('significance');
        return sig ? (30 + sig * 10) : 50;
      },
      'height': function(ele) {
        const sig = ele.data('significance');
        return sig ? (30 + sig * 10) : 50;
      },
      'border-width': 2,
      'border-color': '#5568d3'
    }
  },
  {
    selector: 'edge',
    style: {
      'curve-style': 'bezier',
      'target-arrow-shape': 'triangle',
      'width': function(ele) {
        const sig = ele.data('significance');
        const sources = ele.data('sources') || [];
        const sourceCount = sources.length;
        
        let width = sig ? (1 + sig * 0.8) : 2.5;
        
        if (sourceCount > 1) {
          width += Math.min((sourceCount - 1) * 0.5, 2);
        }
        
        return width;
      },
      'line-color': '#94a3b8',
      'target-arrow-color': '#94a3b8',
      'label': 'data(relation)',
      'font-size': '11px',
      'color': '#374151',
      'text-background-color': '#ffffff',
      'text-background-opacity': 0.8,
      'text-background-padding': 3,
      'edge-text-rotation': 'autorotate'
    }
  },
  {
    selector: 'edge[status = "verified"]',
    style: {
      'line-color': '#059669',
      'target-arrow-color': '#059669',
      'width': 3.5
    }
  },
  {
    selector: 'edge[status = "incorrect"]',
    style: {
      'line-color': '#dc2626',
      'target-arrow-color': '#dc2626',
      'line-style': 'dashed',
      'width': 2
    }
  },
  {
    selector: 'edge[polarity = "negative"]',
    style: {
      'line-style': 'dotted'
    }
  },
  {
    selector: 'node.highlighted',
    style: {
      'background-color': '#dc2626',
      'border-color': '#991b1b',
      'border-width': 4,
      'z-index': 999
    }
  },
  {
    selector: 'node.neighbor',
    style: {
      'background-color': '#f59e0b',
      'border-color': '#d97706',
      'border-width': 3
    }
  },
  {
    selector: 'node.multi-selected',
    style: {
      'background-color': '#8b5cf6',
      'border-color': '#7c3aed',
      'border-width': 4
    }
  },
  {
    selector: 'node.manual-selected',
    style: {
      'background-color': '#10b981',
      'border-color': '#059669',
      'border-width': 4,
      'border-style': 'dashed'
    }
  },
  {
    selector: 'node:selected',
    style: {
      'background-color': '#1d4ed8',
      'border-color': '#1e40af',
      'border-width': 3
    }
  },
  {
    selector: 'edge:selected',
    style: {
      'line-color': '#1d4ed8',
      'target-arrow-color': '#1d4ed8',
      'width': 4
    }
  }
];

export function getLayoutConfig(nodeCount) {
  if (nodeCount > 200) {
    // Large graphs: use faster preset layout first, then refine
    return {
      name: 'cose',
      idealEdgeLength: 80,
      nodeOverlap: 30,
      refresh: 10, // Reduced for performance
      fit: true,
      padding: 20,
      randomize: false,
      componentSpacing: 80,
      nodeRepulsion: 600000,
      edgeElasticity: 80,
      nestingFactor: 5,
      gravity: 100,
      numIter: 300, // Reduced iterations for faster layout
      initialTemp: 150,
      coolingFactor: 0.85, // Faster cooling
      minTemp: 1.0,
      animate: false, // Disable animation for large graphs
      animationDuration: 0
    };
  } else if (nodeCount > 50) {
    return {
      name: 'cose',
      idealEdgeLength: 100,
      nodeOverlap: 20,
      refresh: 15,
      fit: true,
      padding: 30,
      randomize: false,
      componentSpacing: 100,
      nodeRepulsion: 400000,
      edgeElasticity: 100,
      nestingFactor: 5,
      gravity: 80,
      numIter: 600, // Reduced from 1000
      initialTemp: 200,
      coolingFactor: 0.92,
      minTemp: 1.0,
      animate: 'end', // Animate only at end
      animationDuration: 250
    };
  } else {
    return {
      name: 'cose',
      idealEdgeLength: 120,
      nodeOverlap: 10,
      refresh: 20,
      fit: true,
      padding: 40,
      randomize: false,
      componentSpacing: 120,
      nodeRepulsion: 200000,
      edgeElasticity: 120,
      nestingFactor: 5,
      gravity: 80,
      numIter: 600, // Reduced from 800
      initialTemp: 200,
      coolingFactor: 0.95,
      minTemp: 1.0,
      animate: 'end',
      animationDuration: 300
    };
  }
}
