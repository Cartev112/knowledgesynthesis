from fastapi import APIRouter, Response


router = APIRouter()


HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Knowledge Graph Viewer</title>
    <style>
      body { font-family: system-ui, sans-serif; margin: 20px; }
      #graph { width: 100%; height: 70vh; border: 1px solid #ddd; cursor: grab; }
      input { padding: 6px; width: 260px; }
      button { padding: 6px 10px; }
      .legend { margin-top: 10px; color: #334155; font-size: 12px; }
      .legend span { display: inline-block; width: 10px; height: 10px; margin-right: 6px; border-radius: 50%; }
    </style>
  </head>
  <body>
    <h3>Graph Viewer</h3>
    <div>
      <input id="name" placeholder="Entity name (e.g., Vemurafenib)" />
      <button id="load">Load</button>
      <button id="loadAll">Load All</button>
      <span id="status"></span>
    </div>
    <canvas id="graph"></canvas>
    <div class="legend">
      <div><span style="background:#4f46e5"></span>Queried entity</div>
      <div><span style="background:#0ea5e9"></span>Entity</div>
      <div><span style="background:#10b981"></span>Document</div>
    </div>
    <script>
      const canvas = document.getElementById('graph');
      const ctx = canvas.getContext('2d');
      function resize() { canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight; }
      window.addEventListener('resize', resize); resize();

      // pan & zoom state
      let scale = 1;
      let offsetX = 0, offsetY = 0;
      let isPanning = false; let startX = 0, startY = 0;
      canvas.addEventListener('wheel', (e) => {
        e.preventDefault();
        const delta = Math.sign(e.deltaY) * -0.1; // invert for natural feel
        scale = Math.max(0.3, Math.min(3, scale + delta));
        if (lastGraphData) {
          drawAllStatic(lastGraphData);
        } else {
          draw(lastEntity, lastNeighbors);
        }
      }, { passive: false });
      canvas.addEventListener('mousedown', (e) => { isPanning = true; startX = e.clientX; startY = e.clientY; canvas.style.cursor='grabbing'; });
      window.addEventListener('mouseup', () => { isPanning = false; canvas.style.cursor='grab'; });
      window.addEventListener('mousemove', (e) => {
        if (!isPanning) return;
        offsetX += (e.clientX - startX); offsetY += (e.clientY - startY);
        startX = e.clientX; startY = e.clientY;
        if (lastGraphData) {
          drawAllStatic(lastGraphData);
        } else {
          draw(lastEntity, lastNeighbors);
        }
      });

      let lastEntity = null, lastNeighbors = [];
      let lastGraphData = null;

      function draw(entity, neighbors) {
        lastGraphData = null; // Clear full graph data
        lastEntity = entity; lastNeighbors = neighbors;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const cx = canvas.width / 2 + offsetX, cy = canvas.height / 2 + offsetY;
        // center node (queried)
        ctx.beginPath(); ctx.arc(cx, cy, 30*scale, 0, Math.PI*2); ctx.fillStyle = '#4f46e5'; ctx.fill();
        ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.font = `${14*scale}px sans-serif`; ctx.fillText(entity.properties.name, cx, cy+5*scale);
        // neighbors around
        const radius = (Math.min(canvas.width/2, canvas.height/2) - 60) * scale;
        const count = neighbors.length || 1;
        neighbors.forEach((n, i) => {
          const angle = (i / count) * Math.PI * 2;
          const nx = cx + radius * Math.cos(angle);
          const ny = cy + radius * Math.sin(angle);
          // edge
          ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(nx, ny); ctx.strokeStyle = '#94a3b8'; ctx.stroke();
          // edge label
          const midx = (cx + nx)/2, midy = (cy + ny)/2;
          ctx.fillStyle = '#475569'; ctx.font = `${12*scale}px sans-serif`; ctx.textAlign = 'center';
          if (n.relationship) ctx.fillText(n.relationship, midx, midy - 4*scale);
          // node
          const isDoc = (n.node?.labels || []).includes('Document');
          const nodeColor = isDoc ? '#10b981' : '#0ea5e9';
          ctx.beginPath(); ctx.arc(nx, ny, 22*scale, 0, Math.PI*2); ctx.fillStyle = nodeColor; ctx.fill();
          ctx.fillStyle = '#000'; ctx.textAlign = 'center'; ctx.font = `${12*scale}px sans-serif`;
          const label = n.node?.properties?.name || n.node?.properties?.title || 'Node';
          ctx.fillText(label, nx, ny+4*scale);
        });
      }

      // --- Full Graph Drawing ---
      function drawAllStatic(graph) {
        lastGraphData = graph;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const nodeMap = new Map(graph.nodes.map(n => [n.id, n]));

        ctx.save();
        ctx.translate(offsetX, offsetY);
        ctx.scale(scale, scale);

        // Calculate sizes inverse to scale to keep them constant on screen
        const lineWidth = 1 / scale;
        const nodeRadius = 22 / scale;
        const fontSize = 12 / scale;
        ctx.lineWidth = lineWidth;

        // Draw edges first
        graph.relationships.forEach(rel => {
          const source = nodeMap.get(rel.source);
          const target = nodeMap.get(rel.target);
          if (!source || !target) return;
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          ctx.lineTo(target.x, target.y);
          ctx.strokeStyle = '#94a3b8';
          ctx.stroke();
        });
        
        // Draw edge labels on top of edges
        graph.relationships.forEach(rel => {
            const source = nodeMap.get(rel.source);
            const target = nodeMap.get(rel.target);
            if (!source || !target) return;
            const midx = (source.x + target.x) / 2;
            const midy = (source.y + target.y) / 2;
            ctx.font = `${fontSize}px sans-serif`;
            ctx.textAlign = 'center';
            const textMetrics = ctx.measureText(rel.type);
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            ctx.fillRect(midx - textMetrics.width / 2 - 2/scale, midy - fontSize + 2/scale, textMetrics.width + 4/scale, fontSize + 4/scale);
            ctx.fillStyle = '#475569';
            ctx.fillText(rel.type, midx, midy);
        });

        // Draw nodes on top of edges
        graph.nodes.forEach(node => {
          const isDoc = (node.labels || []).includes('Document');
          const nodeColor = isDoc ? '#10b981' : '#0ea5e9';
          ctx.beginPath();
          ctx.arc(node.x, node.y, nodeRadius, 0, Math.PI * 2);
          ctx.fillStyle = nodeColor;
          ctx.fill();
        });

        // Draw node labels on top of nodes
        graph.nodes.forEach(node => {
          ctx.font = `${fontSize}px sans-serif`;
          ctx.textAlign = 'center';
          const label = node.properties?.name || node.properties?.title || 'Node';
          const textMetrics = ctx.measureText(label);
          ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
          ctx.fillRect(node.x - textMetrics.width / 2 - 2/scale, node.y - fontSize / 2 + 4/scale, textMetrics.width + 4/scale, fontSize + 4/scale);
          ctx.fillStyle = '#000';
          ctx.fillText(label, node.x, node.y + 4/scale);
        });
        
        ctx.restore();
      }

      async function layoutAndDrawAll(graph) {
        const status = document.getElementById('status');
        status.textContent = 'Layout...';
        
        // Simple physics-based layout
        const nodes = graph.nodes;
        const relationships = graph.relationships;
        const nodeMap = new Map(nodes.map(n => [n.id, n]));

        nodes.forEach(n => {
          n.x = Math.random() * canvas.width;
          n.y = Math.random() * canvas.height;
          n.vx = 0; n.vy = 0;
        });

        const iterations = 300;
        const repulsion = 80000;
        const stiffness = 0.03;

        for (let i = 0; i < iterations; i++) {
          // Repulsion
          for (let j = 0; j < nodes.length; j++) {
            for (let k = j + 1; k < nodes.length; k++) {
              const n1 = nodes[j], n2 = nodes[k];
              const dx = n2.x - n1.x, dy = n2.y - n1.y;
              const dist = Math.sqrt(dx * dx + dy * dy) || 1;
              const force = repulsion / (dist * dist);
              n1.vx -= force * (dx / dist); n1.vy -= force * (dy / dist);
              n2.vx += force * (dx / dist); n2.vy += force * (dy / dist);
            }
          }
          // Attraction
          relationships.forEach(rel => {
            const source = nodeMap.get(rel.source);
            const target = nodeMap.get(rel.target);
            if (!source || !target) return;
            const dx = target.x - source.x, dy = target.y - source.y;
            source.vx += dx * stiffness; source.vy += dy * stiffness;
            target.vx -= dx * stiffness; target.vy -= dy * stiffness;
          });
          // Update positions
          nodes.forEach(n => {
            n.x += n.vx; n.y += n.vy;
            n.vx *= 0.8; n.vy *= 0.8; // Dampening
          });
        }
        
        // Center the graph
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        nodes.forEach(n => {
            minX = Math.min(minX, n.x);
            maxX = Math.max(maxX, n.x);
            minY = Math.min(minY, n.y);
            maxY = Math.max(maxY, n.y);
        });
        const graphCenterX = minX + (maxX - minX) / 2;
        const graphCenterY = minY + (maxY - minY) / 2;
        nodes.forEach(n => {
            n.x = (n.x - graphCenterX) + canvas.width / 2;
            n.y = (n.y - graphCenterY) + canvas.height / 2;
        });

        drawAllStatic(graph);
      }
      
      async function loadAllGraph() {
        const status = document.getElementById('status');
        status.textContent = 'Loading all...';
        try {
          const res = await fetch('/query/all');
          if (!res.ok) throw new Error(await res.text());
          const data = await res.json();
          await layoutAndDrawAll(data);
          status.textContent = '';
        } catch (e) {
          status.textContent = 'Error: ' + e.message;
        }
      }

      async function loadGraph() {
        const name = document.getElementById('name').value.trim();
        const status = document.getElementById('status');
        if (!name) { status.textContent = 'Enter a name'; return; }
        status.textContent = 'Loading...';
        try {
          const res = await fetch(`/query?name=${encodeURIComponent(name)}`);
          if (!res.ok) throw new Error(await res.text());
          const data = await res.json();
          // normalize neighbors rel name for labels
          const neighbors = (data.neighbors || []).map(n => ({
            relationship: n.relationship,
            node: { labels: n.node?.labels || [], properties: n.node?.properties || {} }
          }));
          draw(data.entity, neighbors);
          status.textContent = '';
        } catch (e) {
          status.textContent = 'Error: ' + e.message;
        }
      }
      document.getElementById('load').addEventListener('click', loadGraph);
      document.getElementById('loadAll').addEventListener('click', loadAllGraph);
    </script>
  </body>
  </html>
""".strip()


@router.get("")
def serve_ui():
    return Response(content=HTML, media_type="text/html")


