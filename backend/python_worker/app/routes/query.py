from fastapi import APIRouter, HTTPException, Query as Q

from ..services.neo4j_client import neo4j_client
from ..core.settings import settings


router = APIRouter()


@router.get("")
def query(name: str = Q(..., min_length=1)):
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
        "RETURN {id: coalesce(n.id, n.name, elementId(n)), label: coalesce(n.label, n.name, n.id), strength: coalesce(n.strength, 0), type: coalesce(n.type, head(labels(n)))} AS node"
    )
    rels_cypher = (
        "MATCH (s:Entity)-[r]->(t:Entity) "
        "RETURN {id: elementId(r), source: coalesce(s.id, s.name), target: coalesce(t.id, t.name), relation: coalesce(r.relation, toLower(type(r))), polarity: coalesce(r.polarity,'positive'), confidence: coalesce(r.confidence,0)} AS relationship"
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
def graph_by_documents(doc_ids: str = Q(..., description="Comma-separated document IDs")):
    ids = [s.strip() for s in doc_ids.split(',') if s.strip()]
    nodes_cypher = (
        "MATCH (d:Document) WHERE d.document_id IN $ids "
        "MATCH (e:Entity)-[:EXTRACTED_FROM]->(d) "
        "RETURN DISTINCT {id: coalesce(e.id, e.name, elementId(e)), label: coalesce(e.label, e.name, e.id), strength: coalesce(e.strength, 0), type: coalesce(e.type, head(labels(e)))} AS node"
    )
    rels_cypher = (
        "MATCH (d:Document) WHERE d.document_id IN $ids "
        "MATCH (s:Entity)-[r]->(t:Entity) "
        "WHERE (s)-[:EXTRACTED_FROM]->(d) OR (t)-[:EXTRACTED_FROM]->(d) "
        "RETURN DISTINCT {id: elementId(r), source: coalesce(s.id, s.name, elementId(s)), target: coalesce(t.id, t.name, elementId(t)), relation: coalesce(r.relation, toLower(type(r))), polarity: coalesce(r.polarity,'positive'), confidence: coalesce(r.confidence,0)} AS relationship"
    )
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            nodes = [rec["node"] for rec in session.run(nodes_cypher, ids=ids)]
            rels = [rec["relationship"] for rec in session.run(rels_cypher, ids=ids)]
            return {"nodes": nodes, "relationships": rels}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch graph: {exc}")


