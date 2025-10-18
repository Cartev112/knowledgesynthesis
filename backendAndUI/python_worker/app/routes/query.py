from fastapi import APIRouter, HTTPException, Query as Q

from ..services.neo4j_client import neo4j_client
from ..core.settings import settings


router = APIRouter()


@router.get("/autocomplete")
def autocomplete(
    q: str = Q(..., min_length=1, description="Partial entity name to autocomplete"),
    limit: int = Q(10, ge=1, le=50),
    page_number: int = Q(1, ge=1, description="Page number for pagination"),
):
    """Lightweight entity autocomplete using case-insensitive prefix/contains match.

    Tries fulltext index if available; falls back to CONTAINS.
    Returns minimal payload for fast UI usage.
    """
    cypher_fulltext_only = """
    CALL db.index.fulltext.queryNodes('entity_search', $fulltext) YIELD node, score
    RETURN {id: coalesce(node.id, node.name, elementId(node)), label: coalesce(node.label, node.name, node.id), type: coalesce(node.type, head(labels(node))), score: score} AS item
    ORDER BY score DESC SKIP $skip LIMIT $limit
    """
    cypher_contains_fallback = """
    MATCH (node:Entity)
    WHERE toLower(node.name) CONTAINS toLower($q)
    RETURN {id: coalesce(node.id, node.name, elementId(node)), label: coalesce(node.label, node.name, node.id), type: coalesce(node.type, head(labels(node))), score: 0.0} AS item
    SKIP $skip LIMIT $limit
    """
    skip = (page_number - 1) * limit
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            try:
                # Try fulltext first (if index exists)
                result = session.run(cypher_fulltext_only, fulltext=q + "*", limit=limit, skip=skip)
                items = [rec["item"] for rec in result]
                # If nothing returned, fall back
                if not items:
                    result2 = session.run(cypher_contains_fallback, q=q, limit=limit, skip=skip)
                    items = [rec["item"] for rec in result2]
                return {"results": items, "page_number": page_number}
            except Exception:
                # Fallback if fulltext not available
                result2 = session.run(cypher_contains_fallback, q=q, limit=limit, skip=skip)
                items = [rec["item"] for rec in result2]
                return {"results": items, "page_number": page_number}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Autocomplete failed: {exc}")


@router.get("")
def query(name: str = Q(..., min_length=1)):
    """
    Legacy single entity query endpoint.
    """
    cypher = (
        "CALL db.index.fulltext.queryNodes('entity_search', $name) YIELD node AS e, score"
        " OPTIONAL MATCH (e)-[r]-(n)"
        " WITH e, score, collect({rel: type(r), other: n}) AS neighbors"
        " RETURN e, neighbors"
        " ORDER BY score DESC"
        " LIMIT 1"
    )
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, name=name)
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Not found")
            e = record["e"]
            neighbors = record["neighbors"]
            return {
                "entity": {
                    "labels": list(e.labels),
                    "properties": dict(e),
                },
                "neighbors": [
                    {
                        "relationship": item["rel"],
                        "node": {
                            "labels": list(item["other"].labels) if item["other"] else [],
                            "properties": dict(item["other"]) if item["other"] else {},
                        },
                    }
                    for item in neighbors
                    if item["other"] is not None
                ],
            }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/all")
def get_all(
    page_number: int = Q(1, ge=1, description="Page number for pagination"),
    limit: int = Q(100, ge=1, le=1000, description="Number of items per page")
):
    """Return all nodes and relationships in the graph (supports legacy and new schemas).
    
    IMPORTANT: Returns relationships only where BOTH source and target nodes are in the result set.
    This prevents orphaned edges that reference nodes outside the pagination window.
    """
    skip = (page_number - 1) * limit
    nodes_cypher = (
        "MATCH (n:Entity) "
        "OPTIONAL MATCH (n)-[:EXTRACTED_FROM]->(doc:Document) "
        "WITH n, collect({id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}) as source_docs "
        "RETURN {id: coalesce(n.id, n.name, elementId(n)), label: coalesce(n.label, n.name, n.id), strength: coalesce(n.strength, 0), type: coalesce(n.type, head(labels(n))), significance: coalesce(n.significance, null), sources: source_docs} AS node "
        "SKIP $skip LIMIT $limit"
    )
    
    # Modified query: Get relationships where BOTH endpoints are in the paginated node set
    rels_cypher = (
        "MATCH (n:Entity) "
        "WITH collect(coalesce(n.id, n.name, elementId(n))) as node_ids "
        "SKIP $skip LIMIT $limit "
        "WITH node_ids "
        "MATCH (s:Entity)-[r]->(t:Entity) "
        "WHERE coalesce(s.id, s.name, elementId(s)) IN node_ids "
        "  AND coalesce(t.id, t.name, elementId(t)) IN node_ids "
        "OPTIONAL MATCH (doc:Document) WHERE doc.document_id IN r.sources "
        "WITH r, s, t, collect({id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}) as source_docs "
        "RETURN {id: elementId(r), source: coalesce(s.id, s.name, elementId(s)), target: coalesce(t.id, t.name, elementId(t)), relation: coalesce(r.relation, toLower(type(r))), polarity: coalesce(r.polarity,'positive'), confidence: coalesce(r.confidence,0), significance: coalesce(r.significance, null), status: r.status, sources: source_docs, page_number: coalesce(r.page_number, null), original_text: coalesce(r.original_text, null), reviewed_by_first_name: coalesce(r.reviewed_by_first_name, null), reviewed_by_last_name: coalesce(r.reviewed_by_last_name, null), reviewed_at: coalesce(r.reviewed_at, null)} AS relationship"
    )
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            nodes_result = session.run(nodes_cypher, skip=skip, limit=limit)
            nodes = [record["node"] for record in nodes_result]

            rels_result = session.run(rels_cypher, skip=skip, limit=limit)
            relationships = [record["relationship"] for record in rels_result]

            return {"nodes": nodes, "relationships": relationships, "page_number": page_number}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph: {exc}")


@router.get("/documents")
def list_documents(
    page_number: int = Q(1, ge=1, description="Page number for pagination"),
    limit: int = Q(50, ge=1, le=500, description="Number of documents per page")
):
    skip = (page_number - 1) * limit
    cypher = "MATCH (d:Document) RETURN d.document_id AS id, d.title AS title ORDER BY d.title SKIP $skip LIMIT $limit"
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, skip=skip, limit=limit)
            documents = [{"id": r["id"], "title": r["title"]} for r in result]
            return {"documents": documents, "page_number": page_number}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {exc}")


@router.get("/graph_by_docs")
def graph_by_documents(
    doc_ids: str = Q(..., description="Comma-separated document IDs"),
    verified_only: bool = Q(False, description="Only include verified relationships"),
    page_number: int = Q(1, ge=1, description="Page number for pagination"),
    limit: int = Q(100, ge=1, le=1000, description="Number of items per page"),
    viewport_bounds: str = Q(None, description="Viewport bounds as 'minX,minY,maxX,maxY' for spatial filtering"),
    center_node_id: str = Q(None, description="Center node ID for neighborhood-based loading")
):
    ids = [s.strip() for s in doc_ids.split(',') if s.strip()]
    skip = (page_number - 1) * limit
    
    # Add status filter if verified_only is True
    status_filter = "AND r.status = 'verified'" if verified_only else ""
    
    nodes_cypher = (
        "MATCH (d:Document) WHERE d.document_id IN $ids "
        "MATCH (e:Entity)-[:EXTRACTED_FROM]->(d) "
        "WITH DISTINCT e "
        "OPTIONAL MATCH (e)-[:EXTRACTED_FROM]->(doc:Document) "
        "WITH e, collect({id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}) as source_docs "
        "RETURN {id: coalesce(e.id, e.name, elementId(e)), label: coalesce(e.label, e.name, e.id), strength: coalesce(e.strength, 0), type: coalesce(e.type, head(labels(e))), significance: coalesce(e.significance, null), sources: source_docs} AS node "
        "SKIP $skip LIMIT $limit"
    )
    rels_cypher = (
        f"MATCH (d:Document) WHERE d.document_id IN $ids "
        f"MATCH (s:Entity)-[r]->(t:Entity) "
        f"WHERE (s)-[:EXTRACTED_FROM]->(d) OR (t)-[:EXTRACTED_FROM]->(d) "
        f"{status_filter} "
        f"WITH r, s, t "
        f"OPTIONAL MATCH (doc:Document) WHERE doc.document_id IN r.sources "
        f"WITH r, s, t, collect({{id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}}) as source_docs "
        f"RETURN DISTINCT {{id: elementId(r), source: coalesce(s.id, s.name, elementId(s)), target: coalesce(t.id, t.name, elementId(t)), relation: coalesce(r.relation, toLower(type(r))), polarity: coalesce(r.polarity,'positive'), confidence: coalesce(r.confidence,0), significance: coalesce(r.significance, null), status: r.status, sources: source_docs, page_number: coalesce(r.page_number, null), original_text: coalesce(r.original_text, null), reviewed_by_first_name: coalesce(r.reviewed_by_first_name, null), reviewed_by_last_name: coalesce(r.reviewed_by_last_name, null), reviewed_at: coalesce(r.reviewed_at, null)}} AS relationship "
        f"SKIP $skip LIMIT $limit"
    )
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            nodes = [rec["node"] for rec in session.run(nodes_cypher, ids=ids, skip=skip, limit=limit)]
            rels = [rec["relationship"] for rec in session.run(rels_cypher, ids=ids, skip=skip, limit=limit)]
            return {"nodes": nodes, "relationships": rels, "page_number": page_number}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph: {exc}")


@router.get("/search/concept")
def search_concept(
    name: str = Q(..., min_length=1, description="Concept name to search for"),
    verified_only: bool = Q(False, description="Only include verified relationships"),
    max_hops: int = Q(1, ge=1, le=3, description="Maximum relationship hops from the concept"),
    page_number: int = Q(1, ge=1, description="Page number for pagination"),
    limit: int = Q(100, ge=1, le=1000, description="Number of items per page")
):
    """
    Advanced cross-document concept search.
    
    Finds a concept by name and returns its relationship graph across all documents.
    Supports filtering by verification status and configurable graph depth.
    """
    skip = (page_number - 1) * limit
    # Simple version without fulltext index requirement
    cypher = """
    MATCH (center:Entity)
    WHERE toLower(center.name) CONTAINS toLower($name)
    WITH center
    LIMIT 10
    
    OPTIONAL MATCH (center)-[r]-(related:Entity)
    WHERE $verified_only = false OR r.status = 'verified'
    
    WITH center, collect(DISTINCT related) AS related_nodes, collect(DISTINCT r) AS rels
    
    WITH [center] + related_nodes AS all_nodes, rels
    
    UNWIND all_nodes AS n
    WITH DISTINCT n, rels
    OPTIONAL MATCH (n)-[:EXTRACTED_FROM]->(doc:Document)
    WITH n, rels, collect({id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}) as source_docs
    WITH collect(DISTINCT {
        id: coalesce(n.id, n.name, elementId(n)),
        label: n.name,
        type: n.type,
        strength: coalesce(n.strength, 0),
        significance: coalesce(n.significance, null),
        sources: source_docs
    }) AS nodes, rels
    
    // Handle case where rels might be empty
    WITH nodes, 
         CASE WHEN size(rels) = 0 THEN []
         ELSE [r IN rels | r]
         END AS valid_rels
    
    UNWIND CASE WHEN size(valid_rels) = 0 THEN [null] ELSE valid_rels END AS r
    
    OPTIONAL MATCH (s)-[r]->(t)
    WHERE r IS NOT NULL
    
    WITH nodes, r, s, t
    WHERE r IS NOT NULL
    
    OPTIONAL MATCH (doc:Document) WHERE doc.document_id IN r.sources
    WITH nodes, r, s, t, collect({id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}) as source_docs
    WITH nodes, collect(DISTINCT {
        id: elementId(r),
        source: coalesce(s.id, s.name, elementId(s)),
        target: coalesce(t.id, t.name, elementId(t)),
        relation: toLower(type(r)),
        confidence: r.confidence,
        significance: coalesce(r.significance, null),
        status: r.status,
        polarity: coalesce(r.polarity, 'positive'),
        sources: source_docs,
        page_number: coalesce(r.page_number, null),
        original_text: coalesce(r.original_text, null),
        reviewed_by_first_name: coalesce(r.reviewed_by_first_name, null),
        reviewed_by_last_name: coalesce(r.reviewed_by_last_name, null),
        reviewed_at: coalesce(r.reviewed_at, null)
    }) AS relationships
    
    // Apply pagination to the final results
    WITH nodes, relationships
    UNWIND nodes AS node
    WITH node, relationships
    SKIP $skip LIMIT $limit
    WITH collect(node) AS paginated_nodes, relationships
    
    RETURN paginated_nodes AS nodes, relationships
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, name=name, verified_only=verified_only, skip=skip, limit=limit)
            record = result.single()
            
            if not record or not record["nodes"]:
                return {"nodes": [], "relationships": [], "message": "No matching concepts found", "page_number": page_number}
            
            return {
                "nodes": record["nodes"],
                "relationships": record["relationships"],
                "search_term": name,
                "verified_only": verified_only,
                "page_number": page_number
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to search concept: {exc}")


@router.get("/viewport")
def get_viewport_graph(
    doc_ids: str = Q(..., description="Comma-separated document IDs"),
    verified_only: bool = Q(False, description="Only include verified relationships"),
    min_x: float = Q(None, description="Minimum X coordinate of viewport"),
    min_y: float = Q(None, description="Minimum Y coordinate of viewport"),
    max_x: float = Q(None, description="Maximum X coordinate of viewport"),
    max_y: float = Q(None, description="Maximum Y coordinate of viewport"),
    zoom_level: float = Q(1.0, description="Current zoom level for detail adjustment"),
    center_node_id: str = Q(None, description="Center node ID for neighborhood-based loading"),
    max_nodes: int = Q(200, ge=50, le=500, description="Maximum number of nodes to return")
):
    """
    Get graph data optimized for viewport-based rendering.
    Returns nodes and relationships within the specified viewport bounds.
    """
    ids = [s.strip() for s in doc_ids.split(',') if s.strip()]
    
    # Add status filter if verified_only is True
    status_filter = "AND r.status = 'verified'" if verified_only else ""
    
    # Build spatial filter if viewport bounds are provided
    spatial_filter = ""
    if min_x is not None and min_y is not None and max_x is not None and max_y is not None:
        spatial_filter = f"AND e.x >= {min_x} AND e.y >= {min_y} AND e.x <= {max_x} AND e.y <= {max_y}"
    
    # Build center node filter for neighborhood loading
    center_filter = ""
    if center_node_id:
        center_filter = f"AND (e.id = '{center_node_id}' OR (e)-[:RELATES_TO*1..2]-(center:Entity {{id: '{center_node_id}'}}))"
    
    # Adjust node limit based on zoom level (fewer nodes when zoomed out)
    adjusted_limit = int(max_nodes / max(zoom_level, 0.5))
    
    nodes_cypher = (
        f"MATCH (d:Document) WHERE d.document_id IN $ids "
        f"MATCH (e:Entity)-[:EXTRACTED_FROM]->(d) "
        f"WITH DISTINCT e "
        f"WHERE 1=1 {spatial_filter} {center_filter} "
        f"OPTIONAL MATCH (e)-[:EXTRACTED_FROM]->(doc:Document) "
        f"WITH e, collect({{id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}}) as source_docs "
        f"RETURN {{id: coalesce(e.id, e.name, elementId(e)), label: coalesce(e.label, e.name, e.id), strength: coalesce(e.strength, 0), type: coalesce(e.type, head(labels(e))), significance: coalesce(e.significance, null), sources: source_docs, x: coalesce(e.x, 0), y: coalesce(e.y, 0)}} AS node "
        f"LIMIT $limit"
    )
    
    # Get relationships for the returned nodes
    rels_cypher = (
        f"MATCH (d:Document) WHERE d.document_id IN $ids "
        f"MATCH (s:Entity)-[r]->(t:Entity) "
        f"WHERE (s)-[:EXTRACTED_FROM]->(d) OR (t)-[:EXTRACTED_FROM]->(d) "
        f"{status_filter} "
        f"WITH r, s, t "
        f"OPTIONAL MATCH (doc:Document) WHERE doc.document_id IN r.sources "
        f"WITH r, s, t, collect({{id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}}) as source_docs "
        f"RETURN DISTINCT {{id: elementId(r), source: coalesce(s.id, s.name, elementId(s)), target: coalesce(t.id, t.name, elementId(t)), relation: coalesce(r.relation, toLower(type(r))), polarity: coalesce(r.polarity,'positive'), confidence: coalesce(r.confidence,0), significance: coalesce(r.significance, null), status: r.status, sources: source_docs, page_number: coalesce(r.page_number, null), original_text: coalesce(r.original_text, null), reviewed_by_first_name: coalesce(r.reviewed_by_first_name, null), reviewed_by_last_name: coalesce(r.reviewed_by_last_name, null), reviewed_at: coalesce(r.reviewed_at, null)}} AS relationship "
        f"LIMIT $rel_limit"
    )
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            nodes = [rec["node"] for rec in session.run(nodes_cypher, ids=ids, limit=adjusted_limit)]
            rels = [rec["relationship"] for rec in session.run(rels_cypher, ids=ids, rel_limit=adjusted_limit * 2)]
            
            return {
                "nodes": nodes, 
                "relationships": rels, 
                "viewport": {
                    "min_x": min_x,
                    "min_y": min_y,
                    "max_x": max_x,
                    "max_y": max_y,
                    "zoom_level": zoom_level
                },
                "total_nodes": len(nodes),
                "total_relationships": len(rels)
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch viewport graph: {exc}")


@router.get("/neighborhood")
def get_node_neighborhood(
    node_id: str = Q(..., description="Node ID to get neighborhood for"),
    max_hops: int = Q(2, ge=1, le=3, description="Maximum relationship hops"),
    verified_only: bool = Q(False, description="Only include verified relationships"),
    limit: int = Q(100, ge=10, le=300, description="Maximum number of nodes to return")
):
    """
    Get the neighborhood around a specific node for incremental loading.
    """
    status_filter = "AND r.status = 'verified'" if verified_only else ""
    
    cypher = f"""
    MATCH (center:Entity)
    WHERE coalesce(center.id, center.name, elementId(center)) = $node_id
    WITH center
    
    OPTIONAL MATCH path = (center)-[r*1..{max_hops}]-(neighbor:Entity)
    WHERE 1=1 {status_filter}
    
    WITH center, collect(DISTINCT neighbor) AS neighbors, collect(DISTINCT r) AS all_rels
    
    WITH [center] + neighbors AS all_nodes, all_rels
    
    UNWIND all_nodes AS n
    WITH DISTINCT n, all_rels
    OPTIONAL MATCH (n)-[:EXTRACTED_FROM]->(doc:Document)
    WITH n, all_rels, collect({{id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}}) as source_docs
    WITH collect(DISTINCT {{
        id: coalesce(n.id, n.name, elementId(n)),
        label: coalesce(n.label, n.name, n.id),
        type: coalesce(n.type, head(labels(n))),
        strength: coalesce(n.strength, 0),
        significance: coalesce(n.significance, null),
        sources: source_docs,
        x: coalesce(n.x, 0),
        y: coalesce(n.y, 0)
    }}) AS nodes, all_rels
    
    UNWIND all_rels AS rel_chain
    UNWIND rel_chain AS r
    WITH nodes, collect(DISTINCT r) AS relationships
    
    RETURN nodes[0..$limit] AS nodes, relationships[0..$rel_limit] AS relationships
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, node_id=node_id, limit=limit, rel_limit=limit * 2)
            record = result.single()
            
            if not record:
                return {"nodes": [], "relationships": [], "center_node_id": node_id}
            
            return {
                "nodes": record["nodes"] or [],
                "relationships": record["relationships"] or [],
                "center_node_id": node_id,
                "max_hops": max_hops
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch neighborhood: {exc}")


@router.post("/subgraph")
def get_subgraph(request: dict):
    """
    Get the subgraph for a set of node IDs.
    Returns all nodes and relationships between them.
    
    Args:
        request: Dict with 'node_ids' list
    """
    from pydantic import BaseModel
    from typing import List
    
    node_ids = request.get('node_ids', [])
    
    if not node_ids:
        return {"nodes": [], "relationships": []}
    
    # Query to get nodes and their relationships
    cypher = """
    MATCH (n:Entity)
    WHERE coalesce(n.id, n.name, elementId(n)) IN $node_ids
    WITH collect(n) as nodes
    UNWIND nodes as n1
    UNWIND nodes as n2
    OPTIONAL MATCH (n1)-[r]->(n2)
    WITH nodes, collect(DISTINCT r) as rels
    RETURN 
        [n IN nodes | {
            id: coalesce(n.id, n.name, elementId(n)),
            label: coalesce(n.label, n.name),
            type: coalesce(n.type, 'Concept'),
            significance: n.significance
        }] as nodes,
        [r IN rels WHERE r IS NOT NULL | {
            id: elementId(r),
            source: coalesce(startNode(r).id, startNode(r).name, elementId(startNode(r))),
            target: coalesce(endNode(r).id, endNode(r).name, elementId(endNode(r))),
            relation: type(r),
            status: coalesce(r.status, 'unverified'),
            significance: r.significance,
            original_text: r.original_text,
            confidence: r.confidence
        }] as relationships
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, node_ids=node_ids)
            record = result.single()
            
            if not record:
                return {"nodes": [], "relationships": []}
            
            return {
                "nodes": record["nodes"],
                "relationships": record["relationships"]
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get subgraph: {exc}")


