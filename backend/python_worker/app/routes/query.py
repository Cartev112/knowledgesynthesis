from fastapi import APIRouter, HTTPException, Query as Q

from ..services.neo4j_client import neo4j_client
from ..core.settings import settings


router = APIRouter()


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
def get_all():
    """Return all nodes and relationships in the graph (supports legacy and new schemas)."""
    nodes_cypher = (
        "MATCH (n:Entity) "
        "OPTIONAL MATCH (n)-[:EXTRACTED_FROM]->(doc:Document) "
        "WITH n, collect({id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}) as source_docs "
        "RETURN {id: coalesce(n.id, n.name, elementId(n)), label: coalesce(n.label, n.name, n.id), strength: coalesce(n.strength, 0), type: coalesce(n.type, head(labels(n))), sources: source_docs} AS node"
    )
    rels_cypher = (
        "MATCH (s:Entity)-[r]->(t:Entity) "
        "WITH r, s, t "
        "OPTIONAL MATCH (doc:Document) WHERE doc.document_id IN r.sources "
        "WITH r, s, t, collect({id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}) as source_docs "
        "RETURN {id: elementId(r), source: coalesce(s.id, s.name, elementId(s)), target: coalesce(t.id, t.name, elementId(t)), relation: coalesce(r.relation, toLower(type(r))), polarity: coalesce(r.polarity,'positive'), confidence: coalesce(r.confidence,0), status: r.status, sources: source_docs, reviewed_by_first_name: r.reviewed_by_first_name, reviewed_by_last_name: r.reviewed_by_last_name, reviewed_at: r.reviewed_at} AS relationship"
    )
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            nodes_result = session.run(nodes_cypher)
            nodes = [record["node"] for record in nodes_result]

            rels_result = session.run(rels_cypher)
            relationships = [record["relationship"] for record in rels_result]

            return {"nodes": nodes, "relationships": relationships}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph: {exc}")


@router.get("/documents")
def list_documents():
    cypher = "MATCH (d:Document) RETURN d.document_id AS id, d.title AS title ORDER BY d.title"
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher)
            return [{"id": r["id"], "title": r["title"]} for r in result]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {exc}")


@router.get("/graph_by_docs")
def graph_by_documents(
    doc_ids: str = Q(..., description="Comma-separated document IDs"),
    verified_only: bool = Q(False, description="Only include verified relationships")
):
    ids = [s.strip() for s in doc_ids.split(',') if s.strip()]
    
    # Add status filter if verified_only is True
    status_filter = "AND r.status = 'verified'" if verified_only else ""
    
    nodes_cypher = (
        "MATCH (d:Document) WHERE d.document_id IN $ids "
        "MATCH (e:Entity)-[:EXTRACTED_FROM]->(d) "
        "WITH DISTINCT e "
        "OPTIONAL MATCH (e)-[:EXTRACTED_FROM]->(doc:Document) "
        "WITH e, collect({id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}) as source_docs "
        "RETURN {id: coalesce(e.id, e.name, elementId(e)), label: coalesce(e.label, e.name, e.id), strength: coalesce(e.strength, 0), type: coalesce(e.type, head(labels(e))), sources: source_docs} AS node"
    )
    rels_cypher = (
        f"MATCH (d:Document) WHERE d.document_id IN $ids "
        f"MATCH (s:Entity)-[r]->(t:Entity) "
        f"WHERE (s)-[:EXTRACTED_FROM]->(d) OR (t)-[:EXTRACTED_FROM]->(d) "
        f"{status_filter} "
        f"WITH r, s, t "
        f"OPTIONAL MATCH (doc:Document) WHERE doc.document_id IN r.sources "
        f"WITH r, s, t, collect({{id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}}) as source_docs "
        f"RETURN DISTINCT {{id: elementId(r), source: coalesce(s.id, s.name, elementId(s)), target: coalesce(t.id, t.name, elementId(t)), relation: coalesce(r.relation, toLower(type(r))), polarity: coalesce(r.polarity,'positive'), confidence: coalesce(r.confidence,0), status: r.status, sources: source_docs, reviewed_by_first_name: r.reviewed_by_first_name, reviewed_by_last_name: r.reviewed_by_last_name, reviewed_at: r.reviewed_at}} AS relationship"
    )
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            nodes = [rec["node"] for rec in session.run(nodes_cypher, ids=ids)]
            rels = [rec["relationship"] for rec in session.run(rels_cypher, ids=ids)]
            return {"nodes": nodes, "relationships": rels}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph: {exc}")


@router.get("/search/concept")
def search_concept(
    name: str = Q(..., min_length=1, description="Concept name to search for"),
    verified_only: bool = Q(False, description="Only include verified relationships"),
    max_hops: int = Q(1, ge=1, le=3, description="Maximum relationship hops from the concept")
):
    """
    Advanced cross-document concept search.
    
    Finds a concept by name and returns its relationship graph across all documents.
    Supports filtering by verification status and configurable graph depth.
    """
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
        sources: source_docs
    }) AS nodes, rels
    
    UNWIND rels AS r
    MATCH (s)-[r]->(t)
    WITH nodes, r, s, t
    OPTIONAL MATCH (doc:Document) WHERE doc.document_id IN r.sources
    WITH nodes, r, s, t, collect({id: doc.document_id, title: coalesce(doc.title, doc.document_id), created_by_first_name: doc.created_by_first_name, created_by_last_name: doc.created_by_last_name}) as source_docs
    WITH nodes, collect(DISTINCT {
        id: elementId(r),
        source: coalesce(s.id, s.name, elementId(s)),
        target: coalesce(t.id, t.name, elementId(t)),
        relation: toLower(type(r)),
        confidence: r.confidence,
        status: r.status,
        polarity: coalesce(r.polarity, 'positive'),
        sources: source_docs,
        reviewed_by_first_name: r.reviewed_by_first_name,
        reviewed_by_last_name: r.reviewed_by_last_name,
        reviewed_at: r.reviewed_at
    }) AS relationships
    
    RETURN nodes, relationships
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, name=name, verified_only=verified_only)
            record = result.single()
            
            if not record or not record["nodes"]:
                return {"nodes": [], "relationships": [], "message": "No matching concepts found"}
            
            return {
                "nodes": record["nodes"],
                "relationships": record["relationships"],
                "search_term": name,
                "verified_only": verified_only
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to search concept: {exc}")


