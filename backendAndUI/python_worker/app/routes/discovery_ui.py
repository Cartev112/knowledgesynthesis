"""
Document Discovery UI
Interface for searching and discovering research papers from PubMed and ArXiv.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()


@router.get("/discovery-ui", response_class=HTMLResponse)
def discovery_ui(request: Request):
    """Render the document discovery interface."""
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Discovery - Knowledge Synthesis</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 20px 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .header h1 {
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .search-panel {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .search-form {
            display: grid;
            gap: 20px;
        }
        
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .form-group label {
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }
        
        .form-group input[type="text"],
        .form-group input[type="number"],
        .form-group select {
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-group input[type="text"]:focus,
        .form-group input[type="number"]:focus,
        .form-group select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .search-options {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .checkbox-group input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        
        .checkbox-group label {
            cursor: pointer;
            font-weight: normal;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        .results-panel {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: none;
        }
        
        .results-panel.active {
            display: block;
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .results-header h2 {
            color: #333;
            font-size: 22px;
        }
        
        .results-count {
            color: #667eea;
            font-weight: 600;
        }
        
        .paper-list {
            display: grid;
            gap: 15px;
        }
        
        .paper-card {
            border: 2px solid #f0f0f0;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s;
            cursor: pointer;
        }
        
        .paper-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
        }
        
        .paper-card.selected {
            border-color: #667eea;
            background: #f8f9ff;
        }
        
        .paper-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 10px;
        }
        
        .paper-title {
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            flex: 1;
        }
        
        .paper-score {
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .paper-meta {
            display: flex;
            gap: 15px;
            margin-bottom: 10px;
            font-size: 13px;
            color: #666;
        }
        
        .paper-meta span {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .paper-abstract {
            font-size: 14px;
            color: #555;
            line-height: 1.6;
            margin-bottom: 10px;
            max-height: 100px;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .paper-abstract.expanded {
            max-height: none;
        }
        
        .paper-actions {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        
        .btn-small {
            padding: 6px 12px;
            font-size: 12px;
        }
        
        .source-badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .source-pubmed {
            background: #e3f2fd;
            color: #1976d2;
        }
        
        .source-arxiv {
            background: #fff3e0;
            color: #f57c00;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .spinner {
            border: 3px solid #f0f0f0;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error-message {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .success-message {
            background: #e8f5e9;
            color: #2e7d32;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .bulk-actions {
            position: sticky;
            bottom: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 -4px 12px rgba(0,0,0,0.1);
            display: none;
            align-items: center;
            justify-content: space-between;
        }
        
        .bulk-actions.active {
            display: flex;
        }
        
        .nav-links {
            display: flex;
            gap: 15px;
            margin-top: 10px;
        }
        
        .nav-links a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }
        
        .nav-links a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Document Discovery</h1>
            <p>Search PubMed and ArXiv for relevant research papers</p>
            <div class="nav-links">
                <a href="/viewer">← Back to Graph Viewer</a>
                <a href="/review-ui">Review Queue</a>
                <a href="/app">Main App</a>
            </div>
        </div>
        
        <div class="search-panel">
            <form class="search-form" id="searchForm">
                <div class="form-group">
                    <label for="query">Research Query</label>
                    <input 
                        type="text" 
                        id="query" 
                        name="query" 
                        placeholder="e.g., BRAF inhibitors in melanoma, machine learning protein folding"
                        required
                    />
                </div>
                
                <div class="search-options">
                    <div class="form-group">
                        <label for="maxResults">Max Results</label>
                        <input type="number" id="maxResults" name="maxResults" value="20" min="1" max="50" />
                    </div>
                    
                    <div class="form-group">
                        <label>Sources</label>
                        <div style="display: flex; gap: 15px; margin-top: 5px;">
                            <div class="checkbox-group">
                                <input type="checkbox" id="sourcePubmed" checked />
                                <label for="sourcePubmed">PubMed</label>
                            </div>
                            <div class="checkbox-group">
                                <input type="checkbox" id="sourceArxiv" checked />
                                <label for="sourceArxiv">ArXiv</label>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <div class="checkbox-group">
                            <input type="checkbox" id="useSemanticRanking" checked />
                            <label for="useSemanticRanking">Use Semantic Ranking (AI-powered relevance)</label>
                        </div>
                    </div>
                </div>
                
                <div class="button-group">
                    <button type="submit" class="btn btn-primary">🔍 Search Papers</button>
                    <button type="button" class="btn btn-secondary" onclick="searchWithGraphContext()">
                        🧠 Search with Graph Context
                    </button>
                </div>
            </form>
        </div>
        
        <div class="results-panel" id="resultsPanel">
            <div class="results-header">
                <h2>Search Results</h2>
                <span class="results-count" id="resultsCount">0 papers found</span>
            </div>
            
            <div id="resultsContainer"></div>
        </div>
        
        <div class="bulk-actions" id="bulkActions">
            <div>
                <strong id="selectedCount">0</strong> papers selected
            </div>
            <div class="button-group">
                <button class="btn btn-secondary btn-small" onclick="clearSelection()">Clear Selection</button>
                <button class="btn btn-primary btn-small" onclick="ingestSelected()">Ingest Selected Papers</button>
            </div>
        </div>
    </div>
    
    <script>
        let searchResults = [];
        let selectedPapers = new Set();
        
        // Search form submission
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await performSearch();
        });
        
        async function performSearch() {
            const query = document.getElementById('query').value;
            const maxResults = parseInt(document.getElementById('maxResults').value);
            const useSemanticRanking = document.getElementById('useSemanticRanking').checked;
            
            const sources = [];
            if (document.getElementById('sourcePubmed').checked) sources.push('pubmed');
            if (document.getElementById('sourceArxiv').checked) sources.push('arxiv');
            
            if (sources.length === 0) {
                alert('Please select at least one source');
                return;
            }
            
            showLoading();
            
            try {
                const response = await fetch('/api/discovery/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query,
                        max_results: maxResults,
                        sources,
                        use_semantic_ranking: useSemanticRanking
                    })
                });
                
                if (!response.ok) throw new Error('Search failed');
                
                const data = await response.json();
                searchResults = data.papers;
                displayResults(data.papers, data.ranked);
                
            } catch (error) {
                showError('Search failed: ' + error.message);
            }
        }
        
        async function searchWithGraphContext() {
            const query = document.getElementById('query').value;
            if (!query) {
                alert('Please enter a research query');
                return;
            }
            
            // Get selected nodes from viewer (if available)
            const selectedNodes = window.opener?.selectedNodes || [];
            const nodeIds = Array.from(selectedNodes);
            
            showLoading();
            
            try {
                const response = await fetch('/api/discovery/search/graph-context', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        query,
                        node_ids: nodeIds.length > 0 ? nodeIds : null,
                        max_results: parseInt(document.getElementById('maxResults').value),
                        use_semantic_ranking: true
                    })
                });
                
                if (!response.ok) throw new Error('Search failed');
                
                const data = await response.json();
                searchResults = data.papers;
                
                let message = '';
                if (data.graph_context_used) {
                    message = `Using context: ${data.entities_in_context} entities, ${data.relationships_in_context} relationships`;
                }
                
                displayResults(data.papers, data.ranked, message);
                
            } catch (error) {
                showError('Graph-context search failed: ' + error.message);
            }
        }
        
        function showLoading() {
            const panel = document.getElementById('resultsPanel');
            const container = document.getElementById('resultsContainer');
            panel.classList.add('active');
            container.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Searching databases...</p>
                </div>
            `;
        }
        
        function showError(message) {
            const panel = document.getElementById('resultsPanel');
            const container = document.getElementById('resultsContainer');
            panel.classList.add('active');
            container.innerHTML = `<div class="error-message">${message}</div>`;
        }
        
        function displayResults(papers, ranked, contextMessage = '') {
            const panel = document.getElementById('resultsPanel');
            const container = document.getElementById('resultsContainer');
            const countEl = document.getElementById('resultsCount');
            
            panel.classList.add('active');
            countEl.textContent = `${papers.length} papers found`;
            
            if (contextMessage) {
                container.innerHTML = `<div class="success-message">${contextMessage}</div>`;
            } else {
                container.innerHTML = '';
            }
            
            if (papers.length === 0) {
                container.innerHTML += '<p style="text-align: center; color: #666; padding: 40px;">No papers found. Try a different query.</p>';
                return;
            }
            
            const listHtml = papers.map((paper, index) => {
                const source = paper.source || 'unknown';
                const title = paper.title || 'Untitled';
                const abstract = paper.abstract || 'No abstract available';
                const authors = paper.authors?.slice(0, 3).join(', ') || 'Unknown authors';
                const year = paper.year || '';
                const score = ranked && paper.relevance_score ? paper.relevance_score : null;
                const paperId = paper.pmid || paper.arxiv_id || index;
                
                return `
                    <div class="paper-card" data-index="${index}" onclick="togglePaperSelection(${index})">
                        <div class="paper-header">
                            <div class="paper-title">${title}</div>
                            ${score !== null ? `<div class="paper-score">${(score * 100).toFixed(0)}% match</div>` : ''}
                        </div>
                        <div class="paper-meta">
                            <span class="source-badge source-${source}">${source}</span>
                            <span>📅 ${year}</span>
                            <span>👥 ${authors}</span>
                        </div>
                        <div class="paper-abstract">${abstract.substring(0, 300)}${abstract.length > 300 ? '...' : ''}</div>
                        <div class="paper-actions">
                            <button class="btn btn-primary btn-small" onclick="event.stopPropagation(); ingestSingle(${index})">
                                ⚡ Ingest Now
                            </button>
                            ${paper.url ? `<a href="${paper.url}" target="_blank" class="btn btn-secondary btn-small" onclick="event.stopPropagation()">View Source</a>` : ''}
                        </div>
                    </div>
                `;
            }).join('');
            
            container.innerHTML += `<div class="paper-list">${listHtml}</div>`;
        }
        
        function togglePaperSelection(index) {
            const card = document.querySelector(`[data-index="${index}"]`);
            
            if (selectedPapers.has(index)) {
                selectedPapers.delete(index);
                card.classList.remove('selected');
            } else {
                selectedPapers.add(index);
                card.classList.add('selected');
            }
            
            updateBulkActions();
        }
        
        function updateBulkActions() {
            const bulkActions = document.getElementById('bulkActions');
            const selectedCount = document.getElementById('selectedCount');
            
            selectedCount.textContent = selectedPapers.size;
            
            if (selectedPapers.size > 0) {
                bulkActions.classList.add('active');
            } else {
                bulkActions.classList.remove('active');
            }
        }
        
        function clearSelection() {
            selectedPapers.clear();
            document.querySelectorAll('.paper-card.selected').forEach(card => {
                card.classList.remove('selected');
            });
            updateBulkActions();
        }
        
        async function ingestSingle(index) {
            const paper = searchResults[index];
            await ingestPapers([paper]);
        }
        
        async function ingestSelected() {
            const papers = Array.from(selectedPapers).map(index => searchResults[index]);
            await ingestPapers(papers);
        }
        
        async function ingestPapers(papers) {
            if (papers.length === 0) return;
            
            const confirmed = confirm(`Ingest ${papers.length} paper(s)? This will extract knowledge and add to the graph.`);
            if (!confirmed) return;
            
            // For now, show alert - actual ingestion will be implemented next
            alert(`Ingestion feature coming soon! Would ingest ${papers.length} papers:\\n\\n` + 
                  papers.map(p => `- ${p.title}`).join('\\n'));
            
            // TODO: Implement actual ingestion via API
            // This will require downloading PDFs (for ArXiv) or using abstracts (for PubMed)
        }
    </script>
</body>
</html>
    """
    
    return HTMLResponse(content=html_content)
