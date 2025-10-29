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
        const ingestButton = document.getElementById('discovery-ingest-button');
        if (ingestButton) {
            ingestButton.addEventListener('click', () => this.ingestFromModal());
        }
        const graphCtxCheckbox = document.getElementById('discovery-use-graph-context');
        if (graphCtxCheckbox) {
            graphCtxCheckbox.addEventListener('change', () => this.updateGraphContextStatus());
        }
        const bulkGraphCtxCheckbox = document.getElementById('discovery-bulk-use-graph-context');
        if (bulkGraphCtxCheckbox) {
            bulkGraphCtxCheckbox.addEventListener('change', () => this.updateBulkGraphContextStatus());
        }
        const ingestParamsModal = document.getElementById('discovery-ingest-modal');
        if (ingestParamsModal) {
            ingestParamsModal.addEventListener('click', (event) => {
                if (event.target === event.currentTarget) {
                    this.closeIngestParamsModal();
                }
            });
        }
        const ingestParamsCloseButton = document.getElementById('discovery-ingest-modal-close');
        if (ingestParamsCloseButton) {
            ingestParamsCloseButton.addEventListener('click', () => this.closeIngestParamsModal());
        }
        const ingestParamsStartButton = document.getElementById('discovery-ingest-modal-start');
        if (ingestParamsStartButton) {
            ingestParamsStartButton.addEventListener('click', () => this.startIngestFromParams());
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
        
        let leftContent = '';
        let rightContent = '';
        
        if (paper.authors && paper.authors.length > 0) {
          leftContent += `
            <div class="discovery-modal-section">
              <div class="discovery-modal-section-title">Authors</div>
              <div class="discovery-modal-section-content">${this.escapeHtml(paper.authors.join(', '))}</div>
            </div>
          `;
        }
        
        leftContent += '<div class="discovery-modal-section"><div class="discovery-modal-section-title">Metadata</div><div class="discovery-modal-meta-grid">';
        if (paper.year) leftContent += `<div class="discovery-modal-meta-label">Year:</div><div class="discovery-modal-meta-value">${paper.year}</div>`;
        if (paper.venue) leftContent += `<div class="discovery-modal-meta-label">Venue:</div><div class="discovery-modal-meta-value">${this.escapeHtml(paper.venue)}</div>`;
        if (paper.journal) leftContent += `<div class="discovery-modal-meta-label">Journal:</div><div class="discovery-modal-meta-value">${this.escapeHtml(paper.journal)}</div>`;
        leftContent += `<div class="discovery-modal-meta-label">Source:</div><div class="discovery-modal-meta-value">${paper.source.replace('_', ' ')}</div>`;
        if (paper.citation_count) leftContent += `<div class="discovery-modal-meta-label">Citations:</div><div class="discovery-modal-meta-value">${paper.citation_count}</div>`;
        if (paper.influential_citation_count) leftContent += `<div class="discovery-modal-meta-label">Influential:</div><div class="discovery-modal-meta-value">${paper.influential_citation_count}</div>`;
        if (paper.doi) leftContent += `<div class="discovery-modal-meta-label">DOI:</div><div class="discovery-modal-meta-value">${this.escapeHtml(paper.doi)}</div>`;
        leftContent += '</div></div>';
        
        if (paper.abstract) {
          rightContent += `
            <div class="discovery-modal-section">
              <div class="discovery-modal-section-title">Abstract</div>
              <div class="discovery-modal-section-content">${this.escapeHtml(paper.abstract)}</div>
            </div>
          `;
        }
        
        const links = [];
        if (paper.url) links.push(`<a href="${paper.url}" target="_blank">View Source</a>`);
        if (paper.pdf_url) links.push(`<a href="${paper.pdf_url}" target="_blank">Download PDF</a>`);
        if (links.length > 0) {
          rightContent += `
            <div class="discovery-modal-section">
              <div class="discovery-modal-section-title">Links</div>
              <div class="discovery-modal-section-content">${links.join(' • ')}</div>
            </div>
          `;
        }
        
        const content = `
          <div class="discovery-modal-two-col">
            <div class="discovery-modal-col">${leftContent}</div>
            <div class="discovery-modal-col">${rightContent}</div>
          </div>
        `;
        
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
            this.openIngestParamsModal(this.currentModalPaper);
        }
    }

    openIngestParamsModal(index) {
        this.currentIngestPaper = index;
        // Close detail modal if open
        const detailOverlay = document.getElementById('discovery-modal-overlay');
        if (detailOverlay) detailOverlay.classList.remove('active');
        // Update graph context status
        this.updateGraphContextStatus();
        // Show params modal
        const modal = document.getElementById('discovery-ingest-modal');
        if (modal) modal.classList.add('visible');
    }

    closeIngestParamsModal() {
        const modal = document.getElementById('discovery-ingest-modal');
        if (modal) modal.classList.remove('visible');
    }

    updateGraphContextStatus() {
        const checkbox = document.getElementById('discovery-use-graph-context');
        const statusDiv = document.getElementById('discovery-graph-context-status');
        const countSpan = document.getElementById('discovery-graph-context-count');
        if (!checkbox || !statusDiv || !countSpan) return;
        if (checkbox.checked) {
            const count = (window.getSelectedNodeCount && window.getSelectedNodeCount()) || 0;
            if (count === 0) {
                alert('Please select nodes in the Viewer first.');
                checkbox.checked = false;
                statusDiv.classList.add('hidden');
            } else {
                countSpan.textContent = count;
                statusDiv.classList.remove('hidden');
                statusDiv.style.display = 'block';
            }
        } else {
            statusDiv.classList.add('hidden');
        }
    }

    async startIngestFromParams() {
        const paper = this.searchResults[this.currentIngestPaper];
        if (!paper) return;
        
        const userContext = document.getElementById('discovery-user-context')?.value?.trim() || '';
        const useGraphContext = document.getElementById('discovery-use-graph-context')?.checked;
        const maxConcepts = parseInt(document.getElementById('discovery-max-concepts')?.value || '100');
        const maxRelationships = parseInt(document.getElementById('discovery-max-relationships')?.value || '50');
        const workspaceId = sessionStorage.getItem('currentWorkspaceId') || null;
        
        let extractionContext = userContext;
        if (useGraphContext) {
            const result = await window.ingestionManager?.getGraphContextText();
            if (result && result.text) {
                extractionContext = extractionContext ? `${result.text}\nUSER FOCUS: ${extractionContext}` : result.text;
            } else {
                alert('Failed to load graph context. Please try again or uncheck the option.');
                return;
            }
        }
        
        // Show progress modal
        window.ingestionManager?.showProgress(true);
        window.ingestionManager?.updateProgress(1, 100, 'Queuing job...');
        
        try {
            let jobId = null;
            if (paper.pdf_url) {
                const response = await fetch('/api/ingest/pdf_url_async', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        pdf_url: paper.pdf_url,
                        document_title: paper.title,
                        max_relationships: maxRelationships,
                        extraction_context: extractionContext || undefined,
                        workspace_id: workspaceId || undefined
                    })
                });
                if (!response.ok) {
                    const err = await response.json().catch(() => ({}));
                    throw new Error(err.detail || 'Failed to queue PDF URL');
                }
                const data = await response.json();
                jobId = data.job_id;
            } else {
                this.closeIngestParamsModal();
                window.ingestionManager?.updateProgress(100, 100, 'Failed');
                alert('No direct PDF URL found for this paper. Please open the source to obtain the PDF and either upload it or paste a direct PDF URL.');
                return;
            }
            
            // Close params modal
            this.closeIngestParamsModal();
            
            // Start polling and update progress modal
            await this.pollDiscoveryJob(jobId, paper.title);
            
        } catch (e) {
            window.ingestionManager?.updateProgress(100, 100, 'Failed');
            alert('Ingestion failed: ' + e.message);
        }
    }

    async pollDiscoveryJob(jobId, paperTitle) {
        const maxAttempts = 300;
        let attempts = 0;
        return new Promise((resolve) => {
            const intId = setInterval(async () => {
                attempts++;
                try {
                    const res = await fetch(`/api/ingest/job/${jobId}`);
                    if (!res.ok) throw new Error('Status check failed');
                    const job = await res.json();
                    if (job.status === 'processing') {
                        window.ingestionManager?.updateProgress(50, 100, `Processing: ${paperTitle}`);
                    } else if (job.status === 'completed') {
                        window.ingestionManager?.updateProgress(100, 100, `Complete: ${paperTitle}`);
                        const workspaceId = job.workspace_id || sessionStorage.getItem('currentWorkspaceId') || null;
                        if (workspaceId) {
                            window.ingestionManager?.notifyWorkspaceUpdated?.(workspaceId);
                        }
                        // Show summary
                        const success = 1;
                        const failed = 0;
                        const written = job.triplets_written || job.triplets_extracted || 0;
                        document.getElementById('progress-summary-success').textContent = success;
                        document.getElementById('progress-summary-failed').textContent = failed;
                        document.getElementById('progress-summary-triplets').textContent = written;
                        document.getElementById('progress-modal-summary').style.display = 'block';
                        document.getElementById('progress-modal-close-btn').textContent = 'Close';
                        clearInterval(intId);
                        resolve(true);
                    } else if (job.status === 'failed') {
                        window.ingestionManager?.updateProgress(100, 100, `Failed: ${paperTitle}`);
                        document.getElementById('progress-summary-success').textContent = 0;
                        document.getElementById('progress-summary-failed').textContent = 1;
                        document.getElementById('progress-summary-triplets').textContent = 0;
                        document.getElementById('progress-modal-summary').style.display = 'block';
                        document.getElementById('progress-modal-close-btn').textContent = 'Close';
                        clearInterval(intId);
                        resolve(false);
                    }
                    if (attempts >= maxAttempts) {
                        clearInterval(intId);
                        resolve(false);
                    }
                } catch (err) {
                    if (attempts >= maxAttempts) {
                        clearInterval(intId);
                        resolve(false);
                    }
                }
            }, 1000);
        });
    }

    async ingestSingle(index) {
        this.openIngestParamsModal(index);
    }

    async ingestSelected() {
        this.openBulkIngestModal();
    }

    openBulkIngestModal() {
        const selected = Array.from(this.selectedPapers).map(i => ({ index: i, paper: this.searchResults[i] })).filter(x => !!x.paper);
        if (selected.length === 0) {
            alert('Please select at least one paper');
            return;
        }
        this.currentBulkSelection = selected;
        this.updateBulkGraphContextStatus();
        const list = document.getElementById('discovery-bulk-list');
        if (list) {
            list.innerHTML = selected.map(({ index, paper }) => `
                <div style="border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px;">
                  <div style="font-weight: 600; margin-bottom: 6px;">${this.escapeHtml(paper.title || 'Untitled')}</div>
                  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                    <div class="form-group" style="margin: 0;">
                      <label>Max Concepts</label>
                      <input type="number" id="bulk-max-concepts-${index}" value="100" min="10" max="500" />
                    </div>
                    <div class="form-group" style="margin: 0;">
                      <label>Max Relationships</label>
                      <input type="number" id="bulk-max-relationships-${index}" value="50" min="10" max="200" />
                    </div>
                    <div class="form-group" style="grid-column: 1 / -1; margin: 0;">
                      <label>User Context (optional)</label>
                      <textarea id="bulk-user-context-${index}" rows="2" placeholder="Optional context for this paper..."></textarea>
                    </div>
                  </div>
                </div>
            `).join('');
        }
        const modal = document.getElementById('discovery-bulk-ingest-modal');
        if (modal) modal.classList.add('visible');
    }

    closeBulkIngestModal() {
        const modal = document.getElementById('discovery-bulk-ingest-modal');
        if (modal) modal.classList.remove('visible');
    }

    updateBulkGraphContextStatus() {
        const checkbox = document.getElementById('discovery-bulk-use-graph-context');
        const statusDiv = document.getElementById('discovery-bulk-graph-context-status');
        const countSpan = document.getElementById('discovery-bulk-graph-context-count');
        if (!checkbox || !statusDiv || !countSpan) return;
        if (checkbox.checked) {
            const count = (window.getSelectedNodeCount && window.getSelectedNodeCount()) || 0;
            if (count === 0) {
                alert('Please select nodes in the Viewer first.');
                checkbox.checked = false;
                statusDiv.classList.add('hidden');
            } else {
                countSpan.textContent = count;
                statusDiv.classList.remove('hidden');
                statusDiv.style.display = 'block';
            }
        } else {
            statusDiv.classList.add('hidden');
        }
    }

    async startBulkIngestFromParams() {
        if (!this.currentBulkSelection || this.currentBulkSelection.length === 0) return;
        const useGraphContext = document.getElementById('discovery-bulk-use-graph-context')?.checked;
        let graphContextText = '';
        if (useGraphContext) {
            const result = await window.ingestionManager?.getGraphContextText();
            if (result && result.text) {
                graphContextText = result.text;
            } else {
                alert('Failed to load graph context. Please try again or uncheck the option.');
                return;
            }
        }
        const workspaceId = sessionStorage.getItem('currentWorkspaceId') || null;
        // Show progress modal
        window.ingestionManager?.showProgress(true);
        window.ingestionManager?.updateProgress(1, 100, 'Queuing jobs...');
        this.closeBulkIngestModal();

        const total = this.currentBulkSelection.length;
        let success = 0, failed = 0, totalWritten = 0;

        // Queue all jobs and track IDs
        const jobs = [];
        for (let i = 0; i < total; i++) {
            const { index, paper } = this.currentBulkSelection[i];
            const maxConcepts = parseInt(document.getElementById(`bulk-max-concepts-${index}`)?.value || '100');
            const maxRelationships = parseInt(document.getElementById(`bulk-max-relationships-${index}`)?.value || '50');
            const userContext = document.getElementById(`bulk-user-context-${index}`)?.value?.trim() || '';
            const extractionContext = graphContextText ? (userContext ? `${graphContextText}\nUSER FOCUS: ${userContext}` : graphContextText) : userContext;
            try {
                let jobId = null;
                if (paper.pdf_url) {
                    const resp = await fetch('/api/ingest/pdf_url_async', {
                        method: 'POST', headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            pdf_url: paper.pdf_url,
                            document_title: paper.title,
                            max_relationships: maxRelationships,
                            extraction_context: extractionContext || undefined,
                            workspace_id: workspaceId || undefined
                        })
                    });
                    if (!resp.ok) throw new Error((await resp.json().catch(() => ({}))).detail || 'Failed to queue PDF');
                    jobId = (await resp.json()).job_id;
                } else {
                    throw new Error('No direct PDF URL');
                }
                jobs.push({ jobId, paperTitle: paper.title });
            } catch (e) {
                failed++;
            }
        }

        // Poll jobs sequentially for simplicity
        for (let i = 0; i < jobs.length; i++) {
            const { jobId, paperTitle } = jobs[i];
            window.ingestionManager?.updateProgress(30 + Math.round((i / jobs.length) * 60), 100, `Processing: ${paperTitle}`);
            const done = await this.pollDiscoveryJob(jobId, paperTitle);
            if (done) {
                success++;
                // After pollDiscoveryJob completes, summary is updated; read triplets if needed
                const tripletsText = document.getElementById('progress-summary-triplets')?.textContent || '0';
                const val = parseInt(tripletsText) || 0;
                totalWritten = Math.max(totalWritten, val); // keep last; accurate per job not tracked here
            } else {
                failed++;
            }
        }

        document.getElementById('progress-summary-success').textContent = success;
        document.getElementById('progress-summary-failed').textContent = failed;
        document.getElementById('progress-summary-triplets').textContent = totalWritten;
        document.getElementById('progress-modal-summary').style.display = 'block';
        document.getElementById('progress-modal-close-btn').textContent = 'Close';
        window.ingestionManager?.updateProgress(100, 100, 'All jobs processed');
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
        const workspaceId = sessionStorage.getItem('currentWorkspaceId') || null;
        const response = await fetch('/api/ingest/pdf_url_async', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pdf_url: paper.pdf_url,
                document_title: paper.title,
                max_relationships: 50,
                workspace_id: workspaceId || undefined
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
        
        const workspaceId = sessionStorage.getItem('currentWorkspaceId') || null;
        const response = await fetch('/api/ingest/text_async', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: textContent,
                document_title: paper.title,
                document_id: paper.pmid || paper.arxiv_id || paper.semantic_scholar_id,
                max_relationships: 30,  // Fewer for abstracts
                workspace_id: workspaceId || undefined
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
