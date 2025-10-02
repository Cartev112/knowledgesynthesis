from __future__ import annotations

from typing import Iterable, Optional

from .neo4j_client import neo4j_client
from ..models.triplet import Triplet


MERGE_TRIPLET_CYPHER = """
MERGE (s:Entity {name: $s_name, type: $s_type})
MERGE (o:Entity {name: $o_name, type: $o_type})
MERGE (d:Document {document_id: $document_id})
ON CREATE SET d.title = coalesce($document_title, d.title),
              d.created_by = $user_id,
              d.created_by_first_name = $user_first_name,
              d.created_by_last_name = $user_last_name,
              d.created_at = datetime()
ON MATCH SET d.updated_at = datetime()
MERGE (s)-[:EXTRACTED_FROM]->(d)
MERGE (o)-[:EXTRACTED_FROM]->(d)
MERGE (s)-[r:%s]->(o)
ON CREATE SET r.sources = [$document_id],
              r.extracted_by = $extracted_by,
              r.confidence = $confidence,
              r.original_text = $original_text,
              r.status = 'unverified',
              r.created_at = datetime(),
              r.created_by = $user_id
ON MATCH SET r.sources = CASE
                WHEN r.sources IS NULL THEN [$document_id]
                WHEN NOT $document_id IN r.sources THEN r.sources + $document_id
                ELSE r.sources
              END,
              r.extracted_by = coalesce(r.extracted_by, $extracted_by),
              r.confidence = CASE WHEN $confidence IS NULL THEN r.confidence ELSE coalesce(r.confidence, $confidence) END,
              r.original_text = coalesce(r.original_text, $original_text),
              r.status = coalesce(r.status, 'unverified'),
              r.updated_at = datetime()
RETURN id(s) AS s_id, id(o) AS o_id, type(r) AS rel_type, r.status AS status
"""


def _write_single(tx, triplet: Triplet, document_id: str, document_title: Optional[str], user_id: Optional[str], user_first_name: Optional[str], user_last_name: Optional[str]) -> dict:
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
        "user_id": user_id or "anonymous",
        "user_first_name": user_first_name or "",
        "user_last_name": user_last_name or "",
    }
    result = tx.run(cypher, **params)
    record = result.single()
    return {
        "subject_id": record["s_id"],
        "object_id": record["o_id"],
        "relationship": record["rel_type"],
        "status": record["status"],
    }


def write_triplets(triplets: Iterable[Triplet], document_id: str, document_title: Optional[str] = None, user_id: Optional[str] = None, user_first_name: Optional[str] = None, user_last_name: Optional[str] = None) -> list[dict]:
    def work(tx):
        outputs = []
        for t in triplets:
            outputs.append(_write_single(tx, t, document_id, document_title, user_id, user_first_name, user_last_name))
        return outputs

    return neo4j_client.execute_write(work)







