"""
Pathway Discovery API Endpoints
================================

Provides advanced graph discovery capabilities:
- Shortest path between concepts
- All paths discovery
- Multi-hop exploration
- Pattern-based queries
"""

from fastapi import APIRouter, HTTPException, Query as Q
from pydantic import BaseModel
from typing import Optional, Dict, Any

from ..services.pathway_discovery import (
    find_shortest_path,
    find_all_paths,
    find_connecting_concepts,
    explore_multi_hop,
    pattern_query
)


router = APIRouter()


@router.get("/shortest-path")
def get_shortest_path(
    source: str = Q(..., min_length=1, description="Source concept name"),
    target: str = Q(..., min_length=1, description="Target concept name"),
    max_hops: int = Q(5, ge=1, le=10, description="Maximum hops to explore"),
    verified_only: bool = Q(False, description="Only consider verified relationships")
):
    """
    Find the shortest path between two concepts in the knowledge graph.
    
    This endpoint reveals how two seemingly unrelated concepts might be connected
    through intermediate relationships, even across multiple documents.
    
    Example: Finding how a drug connects to a disease through genes and pathways.
    """
    try:
        result = find_shortest_path(
            source_name=source,
            target_name=target,
            max_hops=max_hops,
            verified_only=verified_only
        )
        
        if not result["success"]:
            if not result.get("path_found", False):
                return result  # Return with path_found=False, not an error
            raise HTTPException(status_code=400, detail=result.get("error", result.get("message")))
        
        return result
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Shortest path query failed: {exc}")


@router.get("/all-paths")
def get_all_paths(
    source: str = Q(..., min_length=1, description="Source concept name"),
    target: str = Q(..., min_length=1, description="Target concept name"),
    max_hops: int = Q(5, ge=1, le=10, description="Maximum hops to explore"),
    max_paths: int = Q(10, ge=1, le=50, description="Maximum paths to return"),
    verified_only: bool = Q(False, description="Only consider verified relationships")
):
    """
    Find all paths between two concepts (up to max_paths).
    
    Useful for exploring multiple ways concepts are connected and discovering
    alternative relationship pathways.
    """
    try:
        result = find_all_paths(
            source_name=source,
            target_name=target,
            max_hops=max_hops,
            max_paths=max_paths,
            verified_only=verified_only
        )
        
        if not result["success"]:
            return result  # Return with paths_found=0, not an error
        
        return result
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"All paths query failed: {exc}")


@router.get("/connectors")
def get_connecting_concepts(
    source: str = Q(..., min_length=1, description="Source concept name"),
    target: str = Q(..., min_length=1, description="Target concept name"),
    max_hops: int = Q(3, ge=1, le=5, description="Maximum hops from source to connector")
):
    """
    Find intermediate concepts that bridge two entities.
    
    This is particularly useful for discovering "hidden" connections and
    understanding what concepts link two seemingly unrelated entities.
    
    Example: Finding proteins that connect a drug to a disease.
    """
    try:
        result = find_connecting_concepts(
            source_name=source,
            target_name=target,
            max_hops=max_hops
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", result.get("message")))
        
        return result
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Connector query failed: {exc}")


@router.get("/explore")
def explore_from_concept(
    concept: str = Q(..., min_length=1, description="Starting concept name"),
    hops: int = Q(2, ge=1, le=3, description="Number of hops to explore"),
    limit_per_hop: int = Q(10, ge=1, le=50, description="Limit results per hop level"),
    verified_only: bool = Q(False, description="Only consider verified relationships")
):
    """
    Explore the graph starting from a concept, going N hops out.
    
    This provides a neighborhood view of a concept, showing entities at
    different distances (hops) from the starting point.
    
    Useful for discovering the "context" around a concept.
    """
    try:
        result = explore_multi_hop(
            concept_name=concept,
            hops=hops,
            limit_per_hop=limit_per_hop,
            verified_only=verified_only
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", result.get("message")))
        
        return result
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Multi-hop exploration failed: {exc}")


class PatternQueryRequest(BaseModel):
    """Request model for pattern-based queries."""
    node1_type: Optional[str] = None
    node2_type: Optional[str] = None
    relationship: Optional[str] = None
    node1_name: Optional[str] = None
    node2_name: Optional[str] = None
    verified_only: bool = False
    high_confidence: bool = False
    limit: int = 50


@router.post("/pattern")
def query_pattern(request: PatternQueryRequest):
    """
    Execute a pattern-based query.
    
    Allows constructing complex graph patterns like:
    - "Find all Drugs that TARGET Genes that are IMPLICATED_IN Diseases"
    - "Find all Proteins that BIND_TO other Proteins"
    
    This is the foundation for a visual query builder.
    """
    try:
        pattern_config = request.dict()
        result = pattern_query(pattern_config)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", result.get("message")))
        
        return result
        
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pattern query failed: {exc}")


@router.get("/stats")
def get_pathway_stats():
    """
    Get statistics about the graph structure useful for pathway discovery.
    
    Returns metrics like average path length, diameter, and density.
    """
    try:
        from ..services.neo4j_client import neo4j_client
        from ..core.settings import settings
        
        cypher = """
        // Basic graph statistics
        MATCH (n:Entity)
        WITH count(n) AS node_count
        
        MATCH ()-[r]->()
        WITH node_count, count(r) AS rel_count
        
        RETURN 
          node_count,
          rel_count,
          CASE WHEN node_count > 1 
            THEN toFloat(rel_count) / (node_count * (node_count - 1))
            ELSE 0.0 
          END AS density
        """
        
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher)
            record = result.single()
            
            return {
                "node_count": record["node_count"],
                "relationship_count": record["rel_count"],
                "density": round(record["density"], 4),
                "message": "Graph statistics retrieved successfully"
            }
            
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {exc}")


@router.get("/schema")
def get_graph_schema():
    """
    Get all unique node types and relationship types in the graph.
    
    This endpoint extracts the actual schema from your data, which can be
    used to populate dropdowns and build queries dynamically.
    
    Returns:
        Dict with node_types and relationship_types arrays
    """
    try:
        from ..services.neo4j_client import neo4j_client
        from ..core.settings import settings
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info("Schema endpoint called")
        
        # Query node types
        node_types_cypher = """
        MATCH (n:Entity)
        OPTIONAL MATCH (n)-[:IS_A]->(type:Type)
        WITH CASE WHEN type IS NULL THEN 'Concept' ELSE type.name END AS node_type
        RETURN DISTINCT node_type
        ORDER BY node_type
        """
        
        # Query relationship types
        rel_types_cypher = """
        MATCH ()-[r]->()
        RETURN DISTINCT type(r) AS rel_type
        ORDER BY rel_type
        """
        
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            # Get node types
            logger.info("Querying node types...")
            node_result = session.run(node_types_cypher)
            node_types = [record["node_type"] for record in node_result]
            logger.info(f"Found {len(node_types)} node types: {node_types}")
            
            # Get relationship types
            logger.info("Querying relationship types...")
            rel_result = session.run(rel_types_cypher)
            rel_types = [record["rel_type"] for record in rel_result]
            logger.info(f"Found {len(rel_types)} relationship types: {rel_types}")
            
            return {
                "node_types": node_types,
                "relationship_types": rel_types,
                "message": f"Schema retrieved successfully: {len(node_types)} node types, {len(rel_types)} relationship types"
            }
            
    except Exception as exc:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Schema endpoint failed: {exc}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {exc}")

