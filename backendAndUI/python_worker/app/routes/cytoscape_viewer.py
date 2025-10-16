from fastapi import APIRouter, Response


router = APIRouter()


HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Cytoscape Graph Viewer</title>
    <style>
      html, body { height: 100%; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
      #topbar { display: flex; align-items: center; gap: 8px; padding: 10px; border-bottom: 1px solid #ddd; flex-wrap: wrap; }
      #layout { display: grid; grid-template-columns: 3fr 1fr; height: calc(100% - 90px); }
      #cy { width: 100%; height: 100%; }
      #details { border-left: 1px solid #ddd; padding: 12px; overflow: auto; }
      #details h4 { margin: 0 0 8px 0; }
      #details pre { background: #f8fafc; padding: 8px; border: 1px solid #e5e7eb; }
      #search-box { flex: 1; min-width: 200px; padding: 6px 12px; border: 1px solid #d1d5db; border-radius: 4px; }
      .status-badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; }
    </style>
    <script src="https://unpkg.com/cytoscape@3.29.2/dist/cytoscape.min.js"></script>
    <script src="https://unpkg.com/dagre@0.8.5/dist/dagre.min.js"></script>
    <script src="https://unpkg.com/cytoscape-dagre@2.5.0/cytoscape-dagre.js"></script>
  </head>
  <body>
    <div id="topbar">
      <input type="file" id="pdf-upload" accept=".pdf" />
      <button id="process">Ingest PDF</button>
      <select id="doc-select" multiple size="4" style="min-width: 240px;"></select>
      <button id="apply">Apply Selection</button>
      <input type="text" id="search-box" placeholder="Search concept..." />
      <button id="search-btn">Search</button>
      <label style="margin-left:12px;"><input type="checkbox" id="show-negative" checked /> Show negative</label>
      <label><input type="checkbox" id="verified-only" /> Verified only</label>
      <a href="/review-ui" target="_blank" style="margin-left: 8px;">
        <button>Review Queue</button>
      </a>
      <span id="status" style="margin-left:auto"></span>
    </div>
    <div id="layout">
      <div id="cy"></div>
      <div id="details">
        <h4>Details</h4>
        <div id="details-content">Click a node or edge</div>
      </div>
    </div>
    <script>
      cytoscape.use(cytoscapeDagre);

      const el = document.getElementById('cy');
      const status = document.getElementById('status');
      const button = document.getElementById('process');
      const applyBtn = document.getElementById('apply');
      const docSelect = document.getElementById('doc-select');
      const pdfInput = document.getElementById('pdf-upload');
      const details = document.getElementById('details-content');
      const showNegative = document.getElementById('show-negative');
      const verifiedOnly = document.getElementById('verified-only');
      const searchBox = document.getElementById('search-box');
      const searchBtn = document.getElementById('search-btn');

      let cy = cytoscape({
        container: el,
        elements: [],
        wheelSensitivity: 0.2,
        minZoom: 0.1,
        maxZoom: 3,
        style: [
          { selector: 'node', style: {
              'label': 'data(label)',
              'font-size': '10px',
              'text-wrap': 'wrap',
              'text-max-width': 120,
              'background-color': '#94a3b8',
              'width': 'mapData(strength, 0, 3, 24, 48)',
              'height': 'mapData(strength, 0, 3, 16, 28)',
              'text-valign': 'center',
              'text-halign': 'center'
            }
          },
          { selector: 'edge', style: {
              'curve-style': 'bezier',
              'target-arrow-shape': 'triangle',
              'width': 1.5,
              'line-color': '#94a3b8',
              'target-arrow-color': '#94a3b8',
              'label': 'data(relation)',
              'font-size': '9px',
              'text-rotation': 'autorotate',
              'text-margin-y': -10
            }
          },
          { selector: 'edge[polarity = "negative"]', style: {
              'line-style': 'dotted'
            }
          },
          { selector: 'edge[status = "verified"]', style: {
              'line-color': '#059669',
              'target-arrow-color': '#059669',
              'width': 2
            }
          },
          { selector: 'edge[status = "incorrect"]', style: {
              'line-color': '#dc2626',
              'target-arrow-color': '#dc2626',
              'line-style': 'dashed'
            }
          },
          { selector: '.faded', style: { 'opacity': 0.15 } },
          { selector: '.highlight', style: { 'background-color': '#1d4ed8', 'line-color': '#1d4ed8', 'target-arrow-color': '#1d4ed8' } },
          { selector: '.loading', style: { 'opacity': 0.5 } }
        ]
      });

      // Viewport-based loading state
      let currentDocIds = [];
      let isLoading = false;
      let loadedNodes = new Set();
      let viewportUpdateTimeout = null;
      let lastViewport = null;

      function runLayout() {
        cy.layout({ name: 'dagre', rankSep: 80, nodeSep: 40, edgeSep: 10, rankDir: 'LR' }).run();
        cy.fit(undefined, 20);
      }

      function getViewportBounds() {
        const extent = cy.extent();
        return {
          minX: extent.x1,
          minY: extent.y1,
          maxX: extent.x2,
          maxY: extent.y2
        };
      }

      function getZoomLevel() {
        return cy.zoom();
      }

      async function loadViewportData(viewport, zoomLevel, centerNodeId = null) {
        if (isLoading || currentDocIds.length === 0) return;
        
        isLoading = true;
        status.textContent = 'Loading viewport data...';
        
        try {
          const verifiedParam = verifiedOnly.checked ? '&verified_only=true' : '';
          const centerParam = centerNodeId ? `&center_node_id=${encodeURIComponent(centerNodeId)}` : '';
          const url = `/query/viewport?doc_ids=${encodeURIComponent(currentDocIds.join(','))}&min_x=${viewport.minX}&min_y=${viewport.minY}&max_x=${viewport.maxX}&max_y=${viewport.maxY}&zoom_level=${zoomLevel}${verifiedParam}${centerParam}`;
          
          const res = await fetch(url);
          if (!res.ok) throw new Error('Failed to fetch viewport data');
          
          const data = await res.json();
          
          // Add new nodes and edges
          const newElements = toCytoscapeElements(data);
          const existingIds = new Set(cy.elements().map(el => el.id()));
          const elementsToAdd = newElements.filter(el => !existingIds.has(el.data.id));
          
          if (elementsToAdd.length > 0) {
            cy.add(elementsToAdd);
            elementsToAdd.forEach(el => {
              if (el.data.id) loadedNodes.add(el.data.id);
            });
          }
          
          status.textContent = `Loaded ${data.total_nodes} nodes, ${data.total_relationships} edges`;
        } catch (e) {
          status.textContent = 'Error loading viewport: ' + e.message;
        } finally {
          isLoading = false;
        }
      }

      async function loadNodeNeighborhood(nodeId) {
        if (isLoading) return;
        
        isLoading = true;
        status.textContent = 'Loading neighborhood...';
        
        try {
          const verifiedParam = verifiedOnly.checked ? '&verified_only=true' : '';
          const url = `/query/neighborhood?node_id=${encodeURIComponent(nodeId)}&max_hops=2${verifiedParam}`;
          
          const res = await fetch(url);
          if (!res.ok) throw new Error('Failed to fetch neighborhood');
          
          const data = await res.json();
          
          // Add new nodes and edges
          const newElements = toCytoscapeElements(data);
          const existingIds = new Set(cy.elements().map(el => el.id()));
          const elementsToAdd = newElements.filter(el => !existingIds.has(el.data.id));
          
          if (elementsToAdd.length > 0) {
            cy.add(elementsToAdd);
            elementsToAdd.forEach(el => {
              if (el.data.id) loadedNodes.add(el.data.id);
            });
          }
          
          status.textContent = `Loaded neighborhood: ${data.nodes.length} nodes, ${data.relationships.length} edges`;
        } catch (e) {
          status.textContent = 'Error loading neighborhood: ' + e.message;
        } finally {
          isLoading = false;
        }
      }

      function scheduleViewportUpdate() {
        if (viewportUpdateTimeout) {
          clearTimeout(viewportUpdateTimeout);
        }
        
        viewportUpdateTimeout = setTimeout(() => {
          const viewport = getViewportBounds();
          const zoomLevel = getZoomLevel();
          
          // Only update if viewport has changed significantly
          if (!lastViewport || 
              Math.abs(viewport.minX - lastViewport.minX) > 100 ||
              Math.abs(viewport.minY - lastViewport.minY) > 100 ||
              Math.abs(viewport.maxX - lastViewport.maxX) > 100 ||
              Math.abs(viewport.maxY - lastViewport.maxY) > 100 ||
              Math.abs(zoomLevel - lastViewport.zoomLevel) > 0.2) {
            
            lastViewport = { ...viewport, zoomLevel };
            loadViewportData(viewport, zoomLevel);
          }
        }, 500); // Debounce viewport updates
      }

      function toCytoscapeElements(graph) {
        const elements = [];
        for (const n of graph.nodes || []) {
          elements.push({ data: { id: n.id, label: n.label, strength: n.strength ?? 0, type: n.type || 'concept' } });
        }
        for (const e of graph.edges || graph.relationships || []) {
          elements.push({ data: { 
            id: e.id || `${e.source}__${e.relation}__${e.target}`, 
            source: e.source, 
            target: e.target, 
            relation: e.relation, 
            polarity: e.polarity || 'positive', 
            confidence: e.confidence ?? 0,
            status: e.status || 'unverified'
          } });
        }
        return elements;
      }

      async function ingestPdfToDb(file) {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/ingest/pdf', { method: 'POST', body: formData });
        if (!res.ok) throw new Error((await res.json()).detail || 'Failed to ingest PDF');
        return await res.json();
      }

      async function listDocuments() {
        const res = await fetch('/query/documents');
        if (!res.ok) throw new Error('Failed to list documents');
        return await res.json();
      }

      async function fetchGraphForDocs(ids, useViewport = false) {
        if (useViewport) {
          // Use viewport-based loading for better performance
          currentDocIds = ids;
          const viewport = getViewportBounds();
          const zoomLevel = getZoomLevel();
          await loadViewportData(viewport, zoomLevel);
          return { nodes: [], relationships: [] }; // Data is loaded directly into cytoscape
        } else {
          // Traditional loading for initial load
          const verifiedParam = verifiedOnly.checked ? '&verified_only=true' : '';
          const res = await fetch('/query/graph_by_docs?doc_ids=' + encodeURIComponent(ids.join(',')) + verifiedParam);
          if (!res.ok) throw new Error('Failed to fetch graph');
          return await res.json();
        }
      }
      
      async function searchConcept(name) {
        const verifiedParam = verifiedOnly.checked ? '&verified_only=true' : '';
        const res = await fetch('/query/search/concept?name=' + encodeURIComponent(name) + verifiedParam);
        if (!res.ok) throw new Error('Failed to search concept');
        return await res.json();
      }

      async function refreshDocs() {
        const docs = await listDocuments();
        docSelect.innerHTML = '';
        for (const d of docs) {
          const opt = document.createElement('option');
          opt.value = d.id;
          opt.textContent = d.title || d.id;
          docSelect.appendChild(opt);
        }
      }

      function showDetails(el) {
        if (!el) { details.textContent = 'Click a node or edge'; return; }
        const data = el.data();
        if (el.isNode && el.isNode()) {
          details.innerHTML = `<div><strong>Node</strong></div>
            <div>ID: ${data.id}</div>
            <div>Label: ${data.label || ''}</div>
            <div>Type: ${data.type || ''}</div>
            <div>Strength: ${data.strength ?? 0}</div>`;
        } else {
          const statusColor = data.status === 'verified' ? '#059669' : data.status === 'incorrect' ? '#dc2626' : '#d97706';
          details.innerHTML = `<div><strong>Edge</strong></div>
            <div>ID: ${data.id}</div>
            <div>Source: ${data.source}</div>
            <div>Target: ${data.target}</div>
            <div>Relation: ${data.relation || ''}</div>
            <div>Polarity: ${data.polarity || ''}</div>
            <div>Confidence: ${data.confidence ?? 0}</div>
            <div>Status: <span class="status-badge" style="background: ${statusColor}; color: white;">${data.status || 'unverified'}</span></div>`;
        }
      }

      function wireInteractions() {
        cy.on('tap', 'node', (evt) => {
          const node = evt.target;
          cy.elements().removeClass('highlight').addClass('faded');
          node.closedNeighborhood().removeClass('faded').addClass('highlight');
          showDetails(node);
        });
        cy.on('tap', 'edge', (evt) => {
          const edge = evt.target;
          cy.elements().removeClass('highlight').addClass('faded');
          edge.connectedNodes().union(edge).removeClass('faded').addClass('highlight');
          showDetails(edge);
        });
        cy.on('tap', (evt) => {
          if (evt.target === cy) {
            cy.elements().removeClass('faded highlight');
            showDetails(null);
          }
        });
      }

      button.addEventListener('click', async () => {
        const file = pdfInput.files && pdfInput.files[0];
        if (!file) { status.textContent = 'Select a PDF'; return; }
        status.textContent = 'Processing...';
        try {
          const info = await ingestPdfToDb(file);
          await refreshDocs();
          for (const opt of docSelect.options) { opt.selected = (opt.value === info.document_id); }
          const graph = await fetchGraphForDocs([info.document_id]);
          cy.elements().remove();
          cy.add(toCytoscapeElements(graph));
          runLayout();
          wireInteractions();
          const n = (graph.nodes || []).length;
          const m = (graph.relationships || []).length;
          status.textContent = `Done (${n} nodes, ${m} edges)`;
          if (n === 0 && m === 0) {
            console.warn('Ingest returned zero elements. Raw extraction preview:', info.graph);
            details.innerHTML = `<div><strong>Ingested</strong> ${info.title}</div>
              <div>No graph elements found. Check extractor output.</div>`;
          }
        } catch (e) {
          status.textContent = 'Error: ' + e.message;
        }
      });

      applyBtn.addEventListener('click', async () => {
        const selected = Array.from(docSelect.selectedOptions).map(o => o.value);
        if (selected.length === 0) { status.textContent = 'Select one or more documents'; return; }
        status.textContent = 'Loading graph...';
        try {
          const graph = await fetchGraphForDocs(selected);
          cy.elements().remove();
          cy.add(toCytoscapeElements({ nodes: graph.nodes, edges: graph.relationships }));
          runLayout();
          wireInteractions();
          status.textContent = 'Done';
        } catch (e) {
          status.textContent = 'Error: ' + e.message;
        }
      });

      showNegative.addEventListener('change', () => {
        const hide = !showNegative.checked;
        cy.batch(() => {
          cy.edges('[polarity = "negative"]').style('display', hide ? 'none' : 'element');
        });
      });
      
      searchBtn.addEventListener('click', async () => {
        const query = searchBox.value.trim();
        if (!query) { status.textContent = 'Enter a search term'; return; }
        status.textContent = 'Searching...';
        try {
          const graph = await searchConcept(query);
          cy.elements().remove();
          cy.add(toCytoscapeElements({ nodes: graph.nodes, edges: graph.relationships }));
          runLayout();
          wireInteractions();
          status.textContent = `Found ${graph.nodes.length} nodes, ${graph.relationships.length} edges`;
        } catch (e) {
          status.textContent = 'Error: ' + e.message;
        }
      });
      
      searchBox.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') searchBtn.click();
      });

      // Initial load
      refreshDocs().catch(() => {});
      window.addEventListener('resize', () => { cy.resize(); cy.fit(undefined, 20); });
    </script>
  </body>
</html>
""".strip()


@router.get("")
def serve_cytoscape_viewer():
    return Response(content=HTML, media_type="text/html")



