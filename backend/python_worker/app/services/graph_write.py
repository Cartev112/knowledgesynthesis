from __future__ import annotations

from typing import Iterable, Optional

from .neo4j_client import neo4j_client
from ..models.triplet import Triplet


MERGE_TRIPLET_CYPHER = """
MERGE (s:Entity {name: $s_name, type: $s_type})
MERGE (o:Entity {name: $o_name, type: $o_type})
MERGE (d:Document {document_id: $document_id})
ON CREATE SET d.title = coalesce($document_title, d.title)
MERGE (o)-[:EXTRACTED_FROM]->(d)
MERGE (s)-[:EXTRACTED_FROM]->(d)
MERGE (s)-[r:%s {source_document_id: $document_id}]->(o)
ON CREATE SET r.extracted_by = $extracted_by,
              r.confidence_score = $confidence,
              r.original_text = $original_text
RETURN id(s) AS s_id, id(o) AS o_id, type(r) AS rel_type
"""


def _write_single(tx, triplet: Triplet, document_id: str, document_title: Optional[str]) -> dict:
    predicate = triplet.predicate.strip().upper().replace(" ", "_")
    cypher = MERGE_TRIPLET_CYPHER % predicate
    params = {
        "s_name": triplet.subject,
        "s_type": triplet.subject_type or "Entity",
        "o_name": triplet.object,
        "o_type": triplet.object_type or "Entity",
        "document_id": document_id,
        "document_title": document_title,
        "extracted_by": triplet.extracted_by or "system",
        "confidence": triplet.confidence_score,
        "original_text": triplet.original_text,
    }
    result = tx.run(cypher, **params)
    record = result.single()
    return {
        "subject_id": record["s_id"],
        "object_id": record["o_id"],
        "relationship": record["rel_type"],
    }


def write_triplets(triplets: Iterable[Triplet], document_id: str, document_title: Optional[str] = None) -> list[dict]:
    def work(tx):
        outputs = []
        for t in triplets:
            outputs.append(_write_single(tx, t, document_id, document_title))
        return outputs

    return neo4j_client.execute_write(work)







