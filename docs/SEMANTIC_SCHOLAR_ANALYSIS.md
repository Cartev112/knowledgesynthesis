# Semantic Scholar API - Worth It Analysis

## Executive Summary

**Recommendation**: ✅ **YES, absolutely worth implementing**

Semantic Scholar API provides significant advantages over PubMed and ArXiv alone, particularly for:
- **Citation network analysis** (find related papers automatically)
- **Influence metrics** (identify high-impact papers)
- **Full-text availability detection** (find open access versions)
- **Richer metadata** (fields of study, venues, etc.)
- **Cross-domain coverage** (not limited to biomedical or CS/physics)

---

## Semantic Scholar vs. Current Sources

### Comparison Matrix

| Feature | PubMed | ArXiv | **Semantic Scholar** |
|---------|--------|-------|---------------------|
| **Coverage** | 35M+ biomedical | 2M+ preprints | **200M+ papers** (all domains) |
| **Full-text PDFs** | ❌ (paywall) | ✅ Free | ✅ **Open access detection** |
| **Citation data** | Limited | Limited | ✅ **Full citation network** |
| **Influence metrics** | ❌ | ❌ | ✅ **Citation count, influential citations** |
| **Recommendations** | ❌ | ❌ | ✅ **Related papers API** |
| **Fields of study** | MeSH terms | Categories | ✅ **AI-tagged fields** |
| **API rate limit** | 3-10 req/s | 1 req/3s | **100 req/5min (free), 1000/5min (with key)** |
| **Cost** | Free | Free | **Free** (with optional paid tier) |
| **Abstracts** | ✅ | ✅ | ✅ |
| **Author disambiguation** | Limited | ❌ | ✅ **Strong** |
| **Venue information** | ✅ | ❌ | ✅ **Conference/journal rankings** |

### Key Advantages

1. **Citation Network Traversal**
   - Find papers that cite a given paper
   - Find papers cited by a given paper
   - Build comprehensive literature maps
   - **Use case**: "Find all papers that build on this foundational work"

2. **Influence Metrics**
   - Citation count (total citations)
   - Influential citation count (citations from highly-cited papers)
   - **Use case**: Prioritize high-impact papers in search results

3. **Recommendations API**
   - Get papers similar to a given paper
   - Based on content + citation patterns
   - **Use case**: "Find more papers like this one"

4. **Open Access Detection**
   - Automatically finds free PDF versions
   - Links to publisher, arXiv, PubMed Central, etc.
   - **Use case**: Download PDFs for ingestion without paywalls

5. **Cross-Domain Coverage**
   - Not limited to biomedical (PubMed) or CS/physics (ArXiv)
   - Covers chemistry, social sciences, humanities, etc.
   - **Use case**: Interdisciplinary research

---

## API Capabilities

### 1. Paper Search
```http
GET https://api.semanticscholar.org/graph/v1/paper/search?query=BRAF+inhibitors&limit=10
```

**Response includes**:
- Paper ID, title, abstract
- Authors (with IDs for disambiguation)
- Year, venue, fields of study
- Citation count, influential citation count
- Open access PDF URL (if available)
- External IDs (DOI, PubMed ID, ArXiv ID)

### 2. Paper Details
```http
GET https://api.semanticscholar.org/graph/v1/paper/{paperId}?fields=title,authors,citations,references,influentialCitationCount
```

**Additional fields**:
- Full citation list (papers that cite this one)
- Full reference list (papers this one cites)
- Embedding vector (for similarity search)
- TL;DR (AI-generated summary)

### 3. Recommendations
```http
GET https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{paperId}
```

Returns papers similar to the given paper.

### 4. Author Search
```http
GET https://api.semanticscholar.org/graph/v1/author/search?query=Andrew+Ng
```

Find papers by specific authors.

### 5. Bulk Paper Lookup
```http
POST https://api.semanticscholar.org/graph/v1/paper/batch
```

Get details for multiple papers in one request.

---

## Implementation Strategy

### Phase 1: Basic Integration (2-3 hours)

Add Semantic Scholar as a third source alongside PubMed and ArXiv.

**Code changes**:
```python
class SemanticScholarSearcher:
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def search(self, query: str, max_results: int = 20):
        """Search Semantic Scholar for papers."""
        params = {
            "query": query,
            "limit": max_results,
            "fields": "paperId,title,abstract,authors,year,venue,citationCount,influentialCitationCount,openAccessPdf,externalIds"
        }
        response = requests.get(f"{self.BASE_URL}/paper/search", params=params)
        return response.json().get("data", [])
```

**Benefits**:
- Broader coverage than PubMed + ArXiv
- Open access PDF detection
- Influence metrics for ranking

### Phase 2: Citation Network (4-6 hours)

Enable citation-based discovery.

**New features**:
- "Find papers that cite this paper" button
- "Find papers cited by this paper" button
- Citation network visualization in graph viewer
- Automatic traversal: ingest paper → find citing papers → ingest those too

**Use case**:
1. User ingests a foundational paper
2. System finds all papers that cite it
3. User selects relevant ones to ingest
4. Knowledge graph grows systematically

### Phase 3: Recommendations (2-3 hours)

Add "Find similar papers" functionality.

**Implementation**:
```python
def get_recommendations(self, paper_id: str, max_results: int = 10):
    """Get papers similar to the given paper."""
    url = f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/{paper_id}"
    params = {"limit": max_results}
    response = requests.get(url, params=params)
    return response.json().get("recommendedPapers", [])
```

**Use case**:
- User finds one highly relevant paper
- System recommends 10 similar papers
- User ingests the most relevant ones

### Phase 4: Advanced Features (8-10 hours)

**Citation Network Analysis**:
- Identify "hub" papers (highly cited)
- Find "bridge" papers (connect different research areas)
- Detect research trends (citation velocity)

**Author Tracking**:
- Follow specific researchers
- Get alerts when they publish new papers
- Build author collaboration networks

**Field-Based Filtering**:
- Filter by field of study (e.g., only "Machine Learning" papers)
- Cross-domain discovery (e.g., ML + Biology)

---

## Cost Analysis

### Free Tier
- **Rate limit**: 100 requests per 5 minutes
- **Cost**: $0
- **Sufficient for**: Small-scale research, individual users

### Paid Tier (Semantic Scholar API+)
- **Rate limit**: 1000 requests per 5 minutes
- **Cost**: Contact for pricing (typically $0-500/month depending on usage)
- **Needed for**: High-volume automated ingestion, multiple users

### Comparison to Current Costs

**Current** (PubMed + ArXiv + OpenAI embeddings):
- PubMed: Free
- ArXiv: Free
- OpenAI embeddings: ~$0.002 per search (20 papers)
- **Total**: ~$0.002 per search

**With Semantic Scholar**:
- Semantic Scholar: Free
- OpenAI embeddings: ~$0.002 per search
- **Total**: ~$0.002 per search (same!)

**Conclusion**: Adding Semantic Scholar adds **zero cost** while providing significantly more value.

---

## Use Cases Enabled by Semantic Scholar

### 1. Literature Review Automation
**Scenario**: Researcher wants comprehensive review of CRISPR gene editing.

**Workflow**:
1. Search Semantic Scholar for "CRISPR gene editing"
2. Filter by influential citation count (>100 citations)
3. Ingest top 10 papers
4. For each paper, get recommendations
5. Ingest recommended papers
6. Build comprehensive knowledge graph

**Result**: Complete literature map in hours instead of weeks.

### 2. Citation Network Exploration
**Scenario**: User finds a breakthrough paper on protein folding.

**Workflow**:
1. Ingest the breakthrough paper
2. Find all papers that cite it (via Semantic Scholar)
3. Rank by influence metrics
4. Ingest papers that extend the work
5. Visualize citation network in graph viewer

**Result**: Understand how the field evolved after the breakthrough.

### 3. Gap Analysis
**Scenario**: Identify under-researched areas.

**Workflow**:
1. Build knowledge graph from existing papers
2. Identify entities with few relationships
3. Search Semantic Scholar for papers mentioning those entities
4. Discover papers that fill the gaps
5. Ingest to complete the knowledge graph

**Result**: Systematic gap filling.

### 4. Cross-Domain Discovery
**Scenario**: Find connections between machine learning and drug discovery.

**Workflow**:
1. Search Semantic Scholar for "machine learning drug discovery"
2. Filter by fields: ["Machine Learning", "Pharmacology"]
3. Ingest papers that bridge both domains
4. Discover novel applications

**Result**: Interdisciplinary insights.

---

## Technical Implementation

### Updated `document_discovery.py`

```python
class SemanticScholarSearcher:
    """Search and retrieve papers from Semantic Scholar."""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    RECOMMEND_URL = "https://api.semanticscholar.org/recommendations/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.headers = {"x-api-key": api_key} if api_key else {}
    
    def search(self, query: str, max_results: int = 20, fields_of_study: Optional[List[str]] = None) -> List[Dict]:
        """Search for papers."""
        params = {
            "query": query,
            "limit": max_results,
            "fields": "paperId,title,abstract,authors,year,venue,citationCount,influentialCitationCount,openAccessPdf,externalIds,fieldsOfStudy"
        }
        
        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)
        
        response = requests.get(
            f"{self.BASE_URL}/paper/search",
            params=params,
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        
        papers = response.json().get("data", [])
        return [self._format_paper(p) for p in papers]
    
    def get_citations(self, paper_id: str, max_results: int = 100) -> List[Dict]:
        """Get papers that cite this paper."""
        params = {
            "fields": "paperId,title,abstract,authors,year,citationCount",
            "limit": max_results
        }
        
        response = requests.get(
            f"{self.BASE_URL}/paper/{paper_id}/citations",
            params=params,
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        
        citations = response.json().get("data", [])
        return [self._format_paper(c.get("citingPaper", {})) for c in citations]
    
    def get_references(self, paper_id: str, max_results: int = 100) -> List[Dict]:
        """Get papers cited by this paper."""
        params = {
            "fields": "paperId,title,abstract,authors,year,citationCount",
            "limit": max_results
        }
        
        response = requests.get(
            f"{self.BASE_URL}/paper/{paper_id}/references",
            params=params,
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        
        references = response.json().get("data", [])
        return [self._format_paper(r.get("citedPaper", {})) for r in references]
    
    def get_recommendations(self, paper_id: str, max_results: int = 10) -> List[Dict]:
        """Get recommended papers similar to this one."""
        params = {"limit": max_results}
        
        response = requests.get(
            f"{self.RECOMMEND_URL}/papers/forpaper/{paper_id}",
            params=params,
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        
        papers = response.json().get("recommendedPapers", [])
        return [self._format_paper(p) for p in papers]
    
    def _format_paper(self, paper: Dict) -> Dict:
        """Format Semantic Scholar paper to standard format."""
        authors = [a.get("name") for a in paper.get("authors", [])]
        
        # Extract PDF URL
        pdf_url = None
        if paper.get("openAccessPdf"):
            pdf_url = paper["openAccessPdf"].get("url")
        
        # Build URL
        paper_id = paper.get("paperId")
        url = f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else None
        
        return {
            "semantic_scholar_id": paper_id,
            "title": paper.get("title"),
            "abstract": paper.get("abstract"),
            "authors": authors,
            "year": str(paper.get("year", "")),
            "venue": paper.get("venue"),
            "citation_count": paper.get("citationCount", 0),
            "influential_citation_count": paper.get("influentialCitationCount", 0),
            "fields_of_study": paper.get("fieldsOfStudy", []),
            "source": "semantic_scholar",
            "url": url,
            "pdf_url": pdf_url,
            "doi": paper.get("externalIds", {}).get("DOI"),
            "pmid": paper.get("externalIds", {}).get("PubMed"),
            "arxiv_id": paper.get("externalIds", {}).get("ArXiv")
        }
```

### New API Endpoints

```python
@router.get("/paper/{paper_id}/citations")
def get_paper_citations(paper_id: str, max_results: int = 100):
    """Get papers that cite this paper."""
    # Implementation using Semantic Scholar API

@router.get("/paper/{paper_id}/references")
def get_paper_references(paper_id: str, max_results: int = 100):
    """Get papers cited by this paper."""
    # Implementation

@router.get("/paper/{paper_id}/recommendations")
def get_paper_recommendations(paper_id: str, max_results: int = 10):
    """Get recommended papers similar to this one."""
    # Implementation
```

---

## Risks & Mitigation

### Risk 1: Rate Limiting
**Issue**: Free tier limited to 100 requests per 5 minutes.

**Mitigation**:
- Implement request caching
- Add rate limit tracking
- Queue requests if limit approached
- Upgrade to paid tier if needed

### Risk 2: API Changes
**Issue**: Semantic Scholar might change API.

**Mitigation**:
- Use versioned API endpoints (/graph/v1)
- Monitor API changelog
- Implement graceful degradation
- Have fallback to PubMed/ArXiv

### Risk 3: Data Quality
**Issue**: Metadata might be incomplete or incorrect.

**Mitigation**:
- Cross-reference with PubMed/ArXiv when possible
- Allow user to edit metadata
- Flag papers with missing critical fields

---

## Recommendation: Implementation Priority

### High Priority (Do First)
1. ✅ **Basic search integration** - Easy win, immediate value
2. ✅ **Open access PDF detection** - Enables auto-ingestion
3. ✅ **Influence metrics** - Better ranking than pure semantic similarity

### Medium Priority (Do Soon)
4. **Citation network** - High value for literature review
5. **Recommendations API** - Helps users discover related work

### Lower Priority (Nice to Have)
6. **Author tracking** - Useful but not critical
7. **Field-based filtering** - Refinement feature

---

## Conclusion

**Semantic Scholar API is absolutely worth implementing** because:

1. **Zero additional cost** (free tier sufficient for most use cases)
2. **Massive coverage** (200M+ papers vs. 35M PubMed + 2M ArXiv)
3. **Unique features** (citation network, recommendations, influence metrics)
4. **Easy integration** (REST API, similar to PubMed/ArXiv)
5. **High ROI** (2-3 hours implementation for basic integration, huge value)

**Recommended approach**:
- Start with Phase 1 (basic search) - 2-3 hours
- Add Phase 2 (citations) if users find it valuable - 4-6 hours
- Consider Phase 3 (recommendations) for power users - 2-3 hours

**Total effort**: 8-12 hours for full implementation  
**Value**: Transforms platform from "document upload tool" to "intelligent research assistant"

**Next step**: Implement `SemanticScholarSearcher` class and add to discovery service.
