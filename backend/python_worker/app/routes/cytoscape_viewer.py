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
      #topbar { display: flex; align-items: center; gap: 8px; padding: 10px; border-bottom: 1px solid #ddd; }
      #layout { display: grid; grid-template-columns: 3fr 1fr; height: calc(100% - 52px); }
      #cy { width: 100%; height: 100%; }
      #details { border-left: 1px solid #ddd; padding: 12px; overflow: auto; }
      #details h4 { margin: 0 0 8px 0; }
      #details pre { background: #f8fafc; padding: 8px; border: 1px solid #e5e7eb; }
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
      <label style="margin-left:12px;"><input type="checkbox" id="show-negative" checked /> Show negative edges</label>
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

      let cy = cytoscape({
        container: el,
        elements: [],
        wheelSensitivity: 0.2,
        style: [
          { selector: 'node', style: {
              'label': 'data(label)',
              'font-size': '10px',
              'text-wrap': 'wrap',
              'text-max-width': 120,
              'background-color': '#94a3b8',
              'width': 'mapData(strength, 0, 3, 24, 48)',
              'height': 'mapData(strength, 0, 3, 16, 28)'
            }
          },
          { selector: 'edge', style: {
              'curve-style': 'bezier',
              'target-arrow-shape': 'triangle',
              'width': 1.5,
              'line-color': '#94a3b8',
              'target-arrow-color': '#94a3b8',
              'label': 'data(relation)',
              'font-size': '9px'
            }
          },
          { selector: 'edge[polarity = "negative"]', style: {
              'line-style': 'dotted'
            }
          },
          { selector: '.faded', style: { 'opacity': 0.15 } },
          { selector: '.highlight', style: { 'background-color': '#1d4ed8', 'line-color': '#1d4ed8', 'target-arrow-color': '#1d4ed8' } }
        ]
      });

      function runLayout() {
        cy.layout({ name: 'dagre', rankSep: 80, nodeSep: 40, edgeSep: 10, rankDir: 'LR' }).run();
        cy.fit(undefined, 20);
      }

      function toCytoscapeElements(graph) {
        const elements = [];
        for (const n of graph.nodes || []) {
          elements.push({ data: { id: n.id, label: n.label, strength: n.strength ?? 0, type: n.type || 'concept' } });
        }
        for (const e of graph.edges || graph.relationships || []) {
          elements.push({ data: { id: e.id || `${e.source}__${e.relation}__${e.target}`, source: e.source, target: e.target, relation: e.relation, polarity: e.polarity || 'positive', confidence: e.confidence ?? 0 } });
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

      async function fetchGraphForDocs(ids) {
        const res = await fetch('/query/graph_by_docs?doc_ids=' + encodeURIComponent(ids.join(',')));
        if (!res.ok) throw new Error('Failed to fetch graph');
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
          details.innerHTML = `<div><strong>Edge</strong></div>
            <div>ID: ${data.id}</div>
            <div>Source: ${data.source}</div>
            <div>Target: ${data.target}</div>
            <div>Relation: ${data.relation || ''}</div>
            <div>Polarity: ${data.polarity || ''}</div>
            <div>Confidence: ${data.confidence ?? 0}</div>`;
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
          status.textContent = 'Done';
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



