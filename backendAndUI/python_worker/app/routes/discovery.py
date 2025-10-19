"""
Document Discovery API Routes
Endpoints for searching and discovering research papers from external sources.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import logging

from ..services.document_discovery import DocumentDiscoveryService
from ..services.semantic_ranker import SemanticRanker
from ..services.neo4j_client import Neo4jClient
from ..core.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["discovery"])

# Initialize services
discovery_service = DocumentDiscoveryService(
    email="knowledgesynthesis.noreply@gmail.com",  # Default email for API requests
    pubmed_api_key=None  # Can be added to settings later
)
semantic_ranker = SemanticRanker()


class SearchRequest(BaseModel):
    """Request model for document search."""
    query: str = Field(..., description="Search query for finding papers")
    max_results: int = Field(20, ge=1, le=50, description="Maximum number of results")
    sources: Optional[List[str]] = Field(
        None,
        description="Specific sources to search (pubmed, arxiv). If None, searches all."
    )
    use_semantic_ranking: bool = Field(
        True,
        description="Whether to rank results by semantic relevance"
    )
    relevance_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum relevance score (0-1). Only used if semantic ranking is enabled."
    )


class GraphContextRequest(BaseModel):
    """Request model for graph-context-based search."""
    query: str = Field(..., description="Research question or topic")
    node_ids: Optional[List[str]] = Field(
        None,
        description="Optional list of node IDs to use as context"
    )
    max_results: int = Field(20, ge=1, le=50)
    use_semantic_ranking: bool = Field(True)


@router.post("/search")
def search_papers(request: SearchRequest) -> Dict:
    """
    Search for research papers across PubMed and ArXiv.
    
    Returns papers with metadata and optional semantic relevance scores.
    """
    try:
        logger.info(f"Searching for papers: '{request.query}'")
        
        # Search across sources
        if request.sources:
            # Search specific sources
            results = {"pubmed": [], "arxiv": [], "semantic_scholar": []}
            if "pubmed" in request.sources:
                pmids = discovery_service.pubmed.search(request.query, max_results=request.max_results)
                results["pubmed"] = discovery_service.pubmed.get_paper_details(pmids)
            if "arxiv" in request.sources:
                results["arxiv"] = discovery_service.arxiv.search(request.query, max_results=request.max_results)
            if "semantic_scholar" in request.sources:
                results["semantic_scholar"] = discovery_service.semantic_scholar.search(request.query, max_results=request.max_results)
            
            # Combine results
            papers = []
            papers.extend(results.get("pubmed", []))
            papers.extend(results.get("arxiv", []))
            papers.extend(results.get("semantic_scholar", []))
        else:
            # Search all sources
            papers = discovery_service.search_combined(request.query, max_results=request.max_results)
        
        # Apply semantic ranking if requested
        if request.use_semantic_ranking and papers:
            papers = semantic_ranker.rank_papers(papers, query=request.query)
            
            # Apply threshold if specified
            if request.relevance_threshold is not None:
                papers = semantic_ranker.filter_by_threshold(papers, threshold=request.relevance_threshold)
        
        return {
            "query": request.query,
            "total_results": len(papers),
            "papers": papers,
            "ranked": request.use_semantic_ranking
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/search/graph-context")
def search_with_graph_context(request: GraphContextRequest) -> Dict:
    """
    Search for papers relevant to existing knowledge graph context.
    
    Uses selected nodes from the graph to inform search and ranking.
    """
    try:
        logger.info(f"Graph-context search: '{request.query}'")
        
        # Get graph context if node IDs provided
        graph_context = None
        entities = []
        relationships = []
        
        if request.node_ids:
            try:
                neo4j_client = Neo4jClient()
                
                # Get entities
                entity_query = """
                MATCH (n:Entity)
                WHERE coalesce(n.id, n.name, elementId(n)) IN $node_ids
                RETURN n.name as name, n.type as type
                LIMIT 50
                """
                entity_results = neo4j_client.execute_read(entity_query, {"node_ids": request.node_ids})
                entities = [r["name"] for r in entity_results if r.get("name")]
                
                # Get relationships between selected nodes
                rel_query = """
                MATCH (n1:Entity)-[r]->(n2:Entity)
                WHERE coalesce(n1.id, n1.name, elementId(n1)) IN $node_ids
                  AND coalesce(n2.id, n2.name, elementId(n2)) IN $node_ids
                RETURN n1.name as subject, type(r) as predicate, n2.name as object
                LIMIT 20
                """
                rel_results = neo4j_client.execute_read(rel_query, {"node_ids": request.node_ids})
                relationships = [
                    f"{r['subject']} {r['predicate']} {r['object']}"
                    for r in rel_results
                ]
                
                # Build context string
                context_parts = []
                if entities:
                    context_parts.append(f"Entities: {', '.join(entities)}")
                if relationships:
                    context_parts.append(f"Relationships: {'; '.join(relationships)}")
                graph_context = " | ".join(context_parts)
                
                logger.info(f"Using graph context with {len(entities)} entities and {len(relationships)} relationships")
                
            except Exception as e:
                logger.warning(f"Failed to get graph context: {e}")
        
        # Search for papers
        papers = discovery_service.search_combined(request.query, max_results=request.max_results)
        
        # Rank by relevance to query and graph context
        if request.use_semantic_ranking and papers:
            if graph_context:
                papers = semantic_ranker.rank_papers(
                    papers,
                    query=request.query,
                    context=graph_context
                )
            else:
                papers = semantic_ranker.rank_papers(papers, query=request.query)
        
        return {
            "query": request.query,
            "graph_context_used": graph_context is not None,
            "entities_in_context": len(entities),
            "relationships_in_context": len(relationships),
            "total_results": len(papers),
            "papers": papers,
            "ranked": request.use_semantic_ranking
        }
        
    except Exception as e:
        logger.error(f"Graph-context search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/paper/{source}/{paper_id}")
def get_paper_details(source: str, paper_id: str) -> Dict:
    """
    Get detailed information about a specific paper.
    
    Args:
        source: Source database (pubmed or arxiv)
        paper_id: Paper ID (PMID for PubMed, ArXiv ID for ArXiv)
    """
    try:
        if source.lower() == "pubmed":
            papers = discovery_service.pubmed.get_paper_details([paper_id])
            if not papers:
                raise HTTPException(status_code=404, detail="Paper not found")
            return papers[0]
            
        elif source.lower() == "arxiv":
            # For ArXiv, we need to search by ID
            # ArXiv API doesn't have a direct fetch by ID, so we search
            papers = discovery_service.arxiv.search(f"id:{paper_id}", max_results=1)
            if not papers:
                raise HTTPException(status_code=404, detail="Paper not found")
            return papers[0]
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown source: {source}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get paper details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get paper: {str(e)}")


@router.post("/download-pdf")
async def download_paper_pdf(
    source: str,
    paper_id: str,
    background_tasks: BackgroundTasks
) -> Dict:
    """
    Download PDF for a paper (if available).
    
    Currently supports ArXiv. PubMed papers may require institutional access.
    """
    try:
        if source.lower() == "arxiv":
            # Get paper details to find PDF URL
            papers = discovery_service.arxiv.search(f"id:{paper_id}", max_results=1)
            if not papers or not papers[0].get("pdf_url"):
                raise HTTPException(status_code=404, detail="PDF not available")
            
            pdf_url = papers[0]["pdf_url"]
            
            return {
                "status": "available",
                "pdf_url": pdf_url,
                "message": "PDF URL available. Use /ingest/pdf-url endpoint to ingest."
            }
            
        elif source.lower() == "pubmed":
            return {
                "status": "unavailable",
                "message": "PubMed PDFs require institutional access. Please download manually and upload."
            }
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown source: {source}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@router.get("/stats")
def get_discovery_stats() -> Dict:
    """Get statistics about document discovery capabilities."""
    return {
        "available_sources": ["pubmed", "arxiv", "semantic_scholar"],
        "semantic_ranking_available": not settings.openai_dry_run,
        "features": {
            "pubmed": {
                "search": True,
                "metadata": True,
                "pdf_download": False,
                "rate_limit": "3 requests/second without API key, 10 requests/second with API key"
            },
            "arxiv": {
                "search": True,
                "metadata": True,
                "pdf_download": True,
                "rate_limit": "1 request every 3 seconds"
            },
            "semantic_scholar": {
                "search": True,
                "metadata": True,
                "pdf_download": True,
                "citation_data": True,
                "influence_metrics": True,
                "rate_limit": "100 requests per 5 minutes (free), 1000 requests per 5 minutes (with API key)"
            }
        }
    }
