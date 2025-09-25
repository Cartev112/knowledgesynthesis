from __future__ import annotations

from typing import Dict, Iterable

from .neo4j_client import neo4j_client


MERGE_GRAPH_CYPHER = """
// Ensure document node
MERGE (d:Document {document_id: $document_id})
ON CREATE SET d.title = coalesce($document_title, d.title)

WITH d
// Create/merge nodes
UNWIND $nodes AS n
MERGE (e:Entity {id: n.id})
ON CREATE SET e.label = n.label,
              e.name = coalesce(n.label, n.id),
              e.strength = coalesce(n.strength, 0),
              e.type = coalesce(n.type, 'concept')
ON MATCH  SET e.label = coalesce(e.label, n.label),
              e.name = coalesce(e.name, n.label, n.id),
              e.type = coalesce(e.type, n.type, 'concept')
MERGE (e)-[:EXTRACTED_FROM]->(d)
RETURN count(*)
"""


MERGE_EDGES_CYPHER = """
UNWIND $edges AS e
MATCH (s:Entity {id: e.source})
MATCH (t:Entity {id: e.target})
MERGE (s)-[r:REL {relation: e.relation, source_document_id: $document_id}]->(t)
ON CREATE SET r.polarity = coalesce(e.polarity, 'positive'),
              r.confidence = coalesce(e.confidence, 0)
RETURN count(*)
"""


def write_graph_json(graph: Dict, document_id: str, document_title: str | None) -> Dict:
    nodes = list(graph.get("nodes", []))
    edges = list(graph.get("edges", []))

    def work(tx):
        tx.run(MERGE_GRAPH_CYPHER, nodes=nodes, document_id=document_id, document_title=document_title)
        tx.run(MERGE_EDGES_CYPHER, edges=edges, document_id=document_id)
        return {"nodes": len(nodes), "edges": len(edges)}

    return neo4j_client.execute_write(work)


