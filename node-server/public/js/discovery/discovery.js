/**
 * Discovery Manager
 * Handles document discovery from PubMed, ArXiv, and Semantic Scholar
 */

class DiscoveryManager {
    constructor() {
        this.searchResults = [];
        this.selectedPapers = new Set();
        this.init();
    }

    init() {
        // Set up event listeners
        const searchForm = document.getElementById('discovery-search-form');
        if (searchForm) {
            searchForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.performSearch();
            });
        }
    }

    async performSearch() {
        const query = document.getElementById('discovery-query')?.value;
        const maxResults = parseInt(document.getElementById('discovery-max-results')?.value || 20);
        const useSemanticRanking = document.getElementById('discovery-use-semantic-ranking')?.checked;
        
        const sources = [];
        if (document.getElementById('discovery-source-pubmed')?.checked) sources.push('pubmed');
        if (document.getElementById('discovery-source-arxiv')?.checked) sources.push('arxiv');
        if (document.getElementById('discovery-source-semantic-scholar')?.checked) sources.push('semantic_scholar');
        
        if (sources.length === 0) {
            alert('Please select at least one source');
            return;
        }
        
        this.showLoading();
        
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
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Search failed');
            }
            
            const data = await response.json();
            this.searchResults = data.papers;
            this.displayResults(data.papers, data.ranked);
            
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search failed: ' + error.message);
        }
    }

    async searchWithGraphContext() {
        const query = document.getElementById('discovery-query')?.value;
        if (!query) {
            alert('Please enter a research query');
            return;
        }
        
        // Get selected nodes from the viewing tab if available
        const selectedNodes = window.selectedNodes ? Array.from(window.selectedNodes) : [];
        
        this.showLoading();
        
        try {
            const response = await fetch('/api/discovery/search/graph-context', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    node_ids: selectedNodes.length > 0 ? selectedNodes : null,
                    max_results: parseInt(document.getElementById('discovery-max-results')?.value || 20),
                    use_semantic_ranking: true
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Search failed');
            }
            
            const data = await response.json();
            this.searchResults = data.papers;
            
            let message = '';
            if (data.graph_context_used) {
                message = `Using context: ${data.entities_in_context} entities, ${data.relationships_in_context} relationships`;
            }
            
            this.displayResults(data.papers, data.ranked, message);
            
        } catch (error) {
            console.error('Graph-context search error:', error);
            this.showError('Graph-context search failed: ' + error.message);
        }
    }

    showLoading() {
        const panel = document.getElementById('discovery-results-panel');
        const container = document.getElementById('discovery-results-container');
        
        if (panel) panel.classList.add('active');
        if (container) {
            container.innerHTML = `
                <div class="discovery-loading">
                    <div class="discovery-spinner"></div>
                    <p>Searching databases...</p>
                </div>
            `;
        }
    }

    showError(message) {
        const panel = document.getElementById('discovery-results-panel');
        const container = document.getElementById('discovery-results-container');
        
        if (panel) panel.classList.add('active');
        if (container) {
            container.innerHTML = `<div class="discovery-error-message">${this.escapeHtml(message)}</div>`;
        }
    }

    displayResults(papers, ranked, contextMessage = '') {
        const panel = document.getElementById('discovery-results-panel');
        const container = document.getElementById('discovery-results-container');
        const countEl = document.getElementById('discovery-results-count');
        
        if (panel) panel.classList.add('active');
        if (countEl) countEl.textContent = `${papers.length} papers found`;
        
        if (!container) return;
        
        container.innerHTML = '';
        
        if (contextMessage) {
            container.innerHTML = `<div class="discovery-success-message">${this.escapeHtml(contextMessage)}</div>`;
        }
        
        if (papers.length === 0) {
            container.innerHTML += '<p style="text-align: center; color: #666; padding: 40px;">No papers found. Try a different query.</p>';
            return;
        }
        
        const listHtml = papers.map((paper, index) => this.renderPaperCard(paper, index, ranked)).join('');
        container.innerHTML += `<div class="discovery-paper-list">${listHtml}</div>`;
    }

    renderPaperCard(paper, index, ranked) {
        const source = paper.source || 'unknown';
        const title = paper.title || 'Untitled';
        const authors = paper.authors?.slice(0, 2).join(', ') || 'Unknown';
        const year = paper.year || '';
        const score = ranked && paper.relevance_score ? paper.relevance_score : null;
        
        // Citation info for display
        const citationCount = paper.citation_count || 0;
        
        return `
            <div class="discovery-paper-card" data-index="${index}">
                <input 
                    type="checkbox" 
                    class="discovery-paper-checkbox" 
                    data-index="${index}"
                    onchange="window.discoveryManager.togglePaperSelection(${index})"
                />
                <div class="discovery-paper-content">
                    <div class="discovery-paper-title">${this.escapeHtml(title)}</div>
                    <div class="discovery-paper-meta">
                        <span class="discovery-source-badge discovery-source-${source}">${source.replace('_', ' ')}</span>
                        ${year ? `<span>📅 ${year}</span>` : ''}
                        ${authors ? `<span>👥 ${this.escapeHtml(authors)}</span>` : ''}
                        ${citationCount > 0 ? `<span>📚 ${citationCount}</span>` : ''}
                        ${score !== null ? `<span class="discovery-paper-score">${(score * 100).toFixed(0)}%</span>` : ''}
                    </div>
                </div>
                <a href="#" class="discovery-view-details" onclick="event.preventDefault(); window.discoveryManager.showPaperDetails(${index})">
                    View Details →
                </a>
            </div>
        `;
    }

    togglePaperSelection(index) {
        const checkbox = document.querySelector(`.discovery-paper-checkbox[data-index="${index}"]`);
        const card = document.querySelector(`.discovery-paper-card[data-index="${index}"]`);
        
        if (checkbox.checked) {
            this.selectedPapers.add(index);
            card?.classList.add('selected');
        } else {
            this.selectedPapers.delete(index);
            card?.classList.remove('selected');
        }
        
        this.updateIngestButton();
    }

    updateIngestButton() {
        const ingestButton = document.getElementById('discovery-ingest-button');
        const selectedCount = document.getElementById('discovery-selected-count');
        
        if (selectedCount) {
            selectedCount.textContent = this.selectedPapers.size;
        }
        
        if (ingestButton) {
            if (this.selectedPapers.size > 0) {
                ingestButton.style.display = 'block';
            } else {
                ingestButton.style.display = 'none';
            }
        }
    }

    clearSelection() {
        this.selectedPapers.clear();
        document.querySelectorAll('.discovery-paper-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        document.querySelectorAll('.discovery-paper-card.selected').forEach(card => {
            card.classList.remove('selected');
        });
        this.updateIngestButton();
    }

    showPaperDetails(index) {
        const paper = this.searchResults[index];
        if (!paper) return;
        
        this.currentModalPaper = index;
        
        const modal = document.getElementById('discovery-modal-overlay');
        const title = document.getElementById('discovery-modal-title');
        const body = document.getElementById('discovery-modal-body');
        
        title.textContent = paper.title || 'Untitled';
        
        // Build modal content
        let content = '';
        
        // Authors
        if (paper.authors && paper.authors.length > 0) {
            content += `
                <div class="discovery-modal-section">
                    <div class="discovery-modal-section-title">Authors</div>
                    <div class="discovery-modal-section-content">${this.escapeHtml(paper.authors.join(', '))}</div>
                </div>
            `;
        }
        
        // Metadata
        content += '<div class="discovery-modal-section"><div class="discovery-modal-section-title">Metadata</div><div class="discovery-modal-meta-grid">';
        if (paper.year) content += `<div class="discovery-modal-meta-label">Year:</div><div class="discovery-modal-meta-value">${paper.year}</div>`;
        if (paper.venue) content += `<div class="discovery-modal-meta-label">Venue:</div><div class="discovery-modal-meta-value">${this.escapeHtml(paper.venue)}</div>`;
        if (paper.journal) content += `<div class="discovery-modal-meta-label">Journal:</div><div class="discovery-modal-meta-value">${this.escapeHtml(paper.journal)}</div>`;
        content += `<div class="discovery-modal-meta-label">Source:</div><div class="discovery-modal-meta-value">${paper.source.replace('_', ' ')}</div>`;
        if (paper.citation_count) content += `<div class="discovery-modal-meta-label">Citations:</div><div class="discovery-modal-meta-value">${paper.citation_count}</div>`;
        if (paper.influential_citation_count) content += `<div class="discovery-modal-meta-label">Influential:</div><div class="discovery-modal-meta-value">${paper.influential_citation_count}</div>`;
        if (paper.doi) content += `<div class="discovery-modal-meta-label">DOI:</div><div class="discovery-modal-meta-value">${this.escapeHtml(paper.doi)}</div>`;
        content += '</div></div>';
        
        // Abstract
        if (paper.abstract) {
            content += `
                <div class="discovery-modal-section">
                    <div class="discovery-modal-section-title">Abstract</div>
                    <div class="discovery-modal-section-content">${this.escapeHtml(paper.abstract)}</div>
                </div>
            `;
        }
        
        // Links
        const links = [];
        if (paper.url) links.push(`<a href="${paper.url}" target="_blank">View Source</a>`);
        if (paper.pdf_url) links.push(`<a href="${paper.pdf_url}" target="_blank">Download PDF</a>`);
        if (links.length > 0) {
            content += `
                <div class="discovery-modal-section">
                    <div class="discovery-modal-section-title">Links</div>
                    <div class="discovery-modal-section-content">${links.join(' • ')}</div>
                </div>
            `;
        }
        
        body.innerHTML = content;
        modal.classList.add('active');
    }

    closeModal(event) {
        if (event && event.target !== event.currentTarget) return;
        const modal = document.getElementById('discovery-modal-overlay');
        modal.classList.remove('active');
        this.currentModalPaper = null;
    }

    ingestFromModal() {
        if (this.currentModalPaper !== null) {
            this.ingestSingle(this.currentModalPaper);
            this.closeModal();
        }
    }

    async ingestSingle(index) {
        const paper = this.searchResults[index];
        await this.ingestPapers([paper]);
    }

    async ingestSelected() {
        const papers = Array.from(this.selectedPapers).map(index => this.searchResults[index]);
        await this.ingestPapers(papers);
    }

    async ingestPapers(papers) {
        if (papers.length === 0) return;
        
        const confirmed = confirm(`Ingest ${papers.length} paper(s)? This will extract knowledge and add to the graph.`);
        if (!confirmed) return;
        
        // Show progress
        const resultsContainer = document.getElementById('discovery-results-container');
        const progressDiv = document.createElement('div');
        progressDiv.className = 'discovery-success-message';
        progressDiv.innerHTML = `<strong>Ingesting ${papers.length} papers...</strong><br><div id="ingestion-progress"></div>`;
        resultsContainer.insertBefore(progressDiv, resultsContainer.firstChild);
        
        const progressEl = document.getElementById('ingestion-progress');
        const jobIds = [];
        
        // Process each paper
        for (let i = 0; i < papers.length; i++) {
            const paper = papers[i];
            progressEl.innerHTML += `<br>${i + 1}/${papers.length}: ${this.escapeHtml(paper.title)}...`;
            
            try {
                const jobId = await this.ingestSinglePaper(paper);
                if (jobId) {
                    jobIds.push(jobId);
                    progressEl.innerHTML += ` ✅ Queued (Job: ${jobId.substring(0, 8)}...)`;
                } else {
                    progressEl.innerHTML += ` ⚠️ Skipped (no PDF/abstract)`;
                }
            } catch (error) {
                console.error(`Failed to ingest paper: ${paper.title}`, error);
                progressEl.innerHTML += ` ❌ Failed: ${error.message}`;
            }
        }
        
        // Show completion message
        progressDiv.innerHTML = `
            <strong>✅ Ingestion Complete!</strong><br>
            ${jobIds.length} papers queued for processing.<br>
            <small>Check the Review Queue to monitor extraction progress.</small>
        `;
        
        // Clear selection
        this.clearSelection();
    }
    
    async ingestSinglePaper(paper) {
        /**
         * Ingest a single paper based on available content.
         * Priority: PDF URL > Abstract text
         */
        
        // Try PDF URL first (ArXiv, Semantic Scholar open access)
        if (paper.pdf_url) {
            return await this.ingestPdfUrl(paper);
        }
        
        // Fall back to abstract for PubMed or papers without PDFs
        if (paper.abstract && paper.abstract.length > 100) {
            return await this.ingestAbstract(paper);
        }
        
        // No ingestible content
        return null;
    }
    
    async ingestPdfUrl(paper) {
        /**
         * Ingest paper from PDF URL.
         */
        const response = await fetch('/api/ingest/pdf_url_async', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pdf_url: paper.pdf_url,
                document_title: paper.title,
                max_relationships: 50
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'PDF ingestion failed');
        }
        
        const data = await response.json();
        return data.job_id;
    }
    
    async ingestAbstract(paper) {
        /**
         * Ingest paper from abstract text.
         */
        // Build text content with metadata
        const authors = paper.authors?.join(', ') || 'Unknown authors';
        const year = paper.year || 'Unknown year';
        const venue = paper.venue || paper.journal || '';
        
        let textContent = `Title: ${paper.title}\n\n`;
        textContent += `Authors: ${authors}\n`;
        textContent += `Year: ${year}\n`;
        if (venue) textContent += `Published in: ${venue}\n`;
        if (paper.doi) textContent += `DOI: ${paper.doi}\n`;
        textContent += `\nAbstract:\n${paper.abstract}`;
        
        const response = await fetch('/api/ingest/text_async', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: textContent,
                document_title: paper.title,
                document_id: paper.pmid || paper.arxiv_id || paper.semantic_scholar_id,
                max_relationships: 30  // Fewer for abstracts
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Abstract ingestion failed');
        }
        
        const data = await response.json();
        return data.job_id;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize discovery manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.discoveryManager = new DiscoveryManager();
    });
} else {
    window.discoveryManager = new DiscoveryManager();
}
