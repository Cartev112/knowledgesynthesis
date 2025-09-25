from fastapi import APIRouter, Response

router = APIRouter()

HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Mermaid Graph Generator</title>
    <style>
      html, body {
        height: 100%;
        margin: 0;
        padding: 0;
        font-family: system-ui, sans-serif;
        overflow: hidden;
      }
      body {
        display: grid;
        grid-template-columns: 1fr 2fr;
        grid-template-rows: auto minmax(0, 1fr);
        gap: 20px;
        padding: 20px;
        box-sizing: border-box;
        height: 100%;
      }
      .controls { 
        grid-column: 1 / -1;
        display: flex; 
        align-items: center; 
        gap: 10px;
        padding-bottom: 10px;
        border-bottom: 1px solid #ddd;
      }
      .raw-container, .graph-container {
        border: 1px solid #ddd;
        padding: 10px;
        overflow: auto;
        background-color: #f8fafc;
        min-height: 0;
        height: 100%;
      }
      .graph-container {
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      h3 { margin: 0 0 8px 0; }
      #mermaid-graph {
        width: 100%;
        height: 100%;
        min-height: 0;
        flex: 1;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      #mermaid-graph svg { width: 100%; height: 100%; display: block; }
      #status { color: #334155; }
    </style>
  </head>
  <body>
    <div class="controls">
      <h3>Mermaid Graph Generator</h3>
      <input type="file" id="pdf-upload" accept=".pdf">
      <button id="process-button">Process</button>
      <span id="status"></span>
    </div>

    <div class="raw-container">
      <h3>Raw Mermaid Code</h3>
      <pre id="mermaid-raw"></pre>
    </div>

    <div class="graph-container">
      <h3>Rendered Graph</h3>
      <div id="mermaid-graph"></div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
      mermaid.initialize({ startOnLoad: false });

      const processButton = document.getElementById('process-button');
      const pdfUpload = document.getElementById('pdf-upload');
      const status = document.getElementById('status');
      const rawOutput = document.getElementById('mermaid-raw');
      const graphOutput = document.getElementById('mermaid-graph');

      function fitSvgToContainer(svg) {
        if (!svg) return;
        // Remove explicit width/height to allow CSS sizing
        svg.removeAttribute('width');
        svg.removeAttribute('height');
        svg.style.width = '100%';
        svg.style.height = '100%';
        svg.style.maxWidth = '100%';
        svg.style.maxHeight = '100%';
        svg.setAttribute('preserveAspectRatio', 'xMidYMid meet');

        const containerRect = graphOutput.getBoundingClientRect();
        const g = svg.querySelector('g');
        if (!g) return;
        let bbox;
        try { bbox = g.getBBox(); } catch { return; }
        if (!bbox || bbox.width === 0 || bbox.height === 0) return;

        // Compute scale to fit both width and height
        const scaleX = containerRect.width / bbox.width;
        const scaleY = containerRect.height / bbox.height;
        const scale = Math.min(scaleX, scaleY);

        // Center the graph inside the container
        const tx = (containerRect.width - bbox.width * scale) / 2 - bbox.x * scale;
        const ty = (containerRect.height - bbox.height * scale) / 2 - bbox.y * scale;

        g.setAttribute('transform', `translate(${tx},${ty}) scale(${scale})`);
      }

      async function renderMermaid(mermaidCode) {
        const { svg } = await mermaid.render('graph-div', mermaidCode);
        graphOutput.innerHTML = svg;
        // Defer fitting to ensure DOM is ready
        requestAnimationFrame(() => fitSvgToContainer(graphOutput.querySelector('svg')));
      }

      processButton.addEventListener('click', async () => {
        const file = pdfUpload.files[0];
        if (!file) {
          status.textContent = 'Please select a PDF file.';
          return;
        }

        const formData = new FormData();
        formData.append('file', file);

        status.textContent = 'Processing PDF... This may take a moment.';
        rawOutput.textContent = '';
        graphOutput.innerHTML = '';

        try {
          const response = await fetch('/process/pdf-to-mermaid', {
            method: 'POST',
            body: formData,
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to process PDF.');
          }

          const data = await response.json();
          const mermaidCode = data.graph;

          rawOutput.textContent = mermaidCode;
          await renderMermaid(mermaidCode);
          status.textContent = `Processed ${data.filename} successfully.`;

        } catch (error) {
          status.textContent = 'Error: ' + error.message;
        }
      });

      // Re-fit on window resize in case layout changes
      window.addEventListener('resize', () => fitSvgToContainer(graphOutput.querySelector('svg')));
    </script>
  </body>
</html>
""".strip()

@router.get("")
def serve_mermaid_viewer():
    return Response(content=HTML, media_type="text/html")
