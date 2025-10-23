from __future__ import annotations

from typing import Iterable, Optional
import logging

from .neo4j_client import neo4j_client
from .entity_consolidation import consolidate_identical_entities
from ..models.triplet import Triplet

logger = logging.getLogger(__name__)


MERGE_TRIPLET_CYPHER = """
MERGE (s:Entity {name: $s_name, type: $s_type})
ON CREATE SET s.created_by = $user_id,
              s.created_by_first_name = $user_first_name,
              s.created_by_last_name = $user_last_name,
              s.created_at = datetime(),
              s.significance = $s_significance
ON MATCH SET s.updated_at = datetime(),
             s.significance = CASE 
                WHEN $s_significance IS NOT NULL AND ($s_significance > coalesce(s.significance, 0)) 
                THEN $s_significance 
                ELSE coalesce(s.significance, $s_significance) 
             END

MERGE (o:Entity {name: $o_name, type: $o_type})
ON CREATE SET o.created_by = $user_id,
              o.created_by_first_name = $user_first_name,
              o.created_by_last_name = $user_last_name,
              o.created_at = datetime(),
              o.significance = $o_significance
ON MATCH SET o.updated_at = datetime(),
             o.significance = CASE 
                WHEN $o_significance IS NOT NULL AND ($o_significance > coalesce(o.significance, 0)) 
                THEN $o_significance 
                ELSE coalesce(o.significance, $o_significance) 
             END
MERGE (d:Document {document_id: $document_id})
ON CREATE SET d.title = coalesce($document_title, d.title),
              d.created_by = $user_id,
              d.created_by_first_name = $user_first_name,
              d.created_by_last_name = $user_last_name,
              d.created_at = datetime()
ON MATCH SET d.updated_at = datetime(),
              d.title = coalesce($document_title, d.title),
              d.created_by = $user_id,
              d.created_by_first_name = $user_first_name,
              d.created_by_last_name = $user_last_name
MERGE (s)-[:EXTRACTED_FROM]->(d)
MERGE (o)-[:EXTRACTED_FROM]->(d)
MERGE (s)-[r:%s]->(o)
ON CREATE SET r.sources = [$document_id],
              r.extracted_by = $extracted_by,
              r.confidence = $confidence,
              r.original_text = $original_text,
              r.polarity = $polarity,
              r.status = 'unverified',
              r.significance = $r_significance,
              r.page_number = $page_number,
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
              r.polarity = coalesce(r.polarity, $polarity),
              r.status = coalesce(r.status, 'unverified'),
              r.significance = CASE 
                WHEN $r_significance IS NOT NULL AND ($r_significance > coalesce(r.significance, 0)) 
                THEN $r_significance 
                ELSE coalesce(r.significance, $r_significance) 
              END,
              r.page_number = coalesce(r.page_number, $page_number),
              r.updated_at = datetime()
RETURN elementId(s) AS s_id, elementId(o) AS o_id, type(r) AS rel_type, r.status AS status
"""


def _write_single(tx, triplet: Triplet, document_id: str, document_title: Optional[str], user_id: Optional[str], user_first_name: Optional[str], user_last_name: Optional[str]) -> dict:
    predicate = triplet.predicate.strip().upper().replace(" ", "_")
    
    # Determine polarity based on predicate
    polarity = "positive"  # default
    if predicate.lower().startswith("does_not_"):
        polarity = "negative"
    
    # User info will now be set directly in the main Cypher query
    
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
        "polarity": polarity,
        "user_id": user_id or "anonymous",
        "user_first_name": user_first_name or "",
        "user_last_name": user_last_name or "",
        "s_significance": triplet.subject_significance,
        "o_significance": triplet.object_significance,
        "r_significance": triplet.relationship_significance,
        "page_number": triplet.page_number,
    }
    result = tx.run(cypher, **params)
    record = result.single()
    
    # Log what happened with page number info
    page_info = f" [page {triplet.page_number}]" if triplet.page_number else " [no page]"
    logger.debug(f"Wrote/merged: ({triplet.subject})-[{predicate}]->({triplet.object}){page_info}")
    
    return {
        "subject_id": record["s_id"],
        "object_id": record["o_id"],
        "relationship": record["rel_type"],
        "status": record["status"],
        "page_number": triplet.page_number,  # Include in response for verification
    }


def write_triplets(triplets: Iterable[Triplet], document_id: str, document_title: Optional[str] = None, user_id: Optional[str] = None, user_first_name: Optional[str] = None, user_last_name: Optional[str] = None, workspace_id: Optional[str] = None, consolidate_entities: bool = True) -> list[dict]:
    """
    Write triplets to the graph and optionally consolidate identical entities.
    
    Args:
        triplets: Iterable of Triplet objects to write
        document_id: Document identifier
        document_title: Optional document title
        user_id: Optional user ID
        user_first_name: Optional user first name
        user_last_name: Optional user last name
        workspace_id: Optional workspace ID to associate document with
        consolidate_entities: Whether to run APOC consolidation after writing
        
    Returns:
        List of write results plus consolidation results if applicable
    """
    def work(tx):
        outputs = []
        for t in triplets:
            outputs.append(_write_single(tx, t, document_id, document_title, user_id, user_first_name, user_last_name))
        
        # Associate document with workspace if provided
        if workspace_id:
            tx.run(
                """
                MATCH (d:Document {document_id: $document_id})
                MATCH (w:Workspace {workspace_id: $workspace_id})
                MERGE (d)-[:BELONGS_TO]->(w)
                """,
                document_id=document_id,
                workspace_id=workspace_id
            )
            logger.info(f"Associated document {document_id} with workspace {workspace_id}")
        
        return outputs

    # Write triplets first
    write_results = neo4j_client.execute_write(work)
    
    # Run APOC consolidation if requested and APOC is available
    consolidation_results = None
    if consolidate_entities:
        try:
            logger.info("Running APOC entity consolidation after triplet ingestion")
            consolidation_results = consolidate_identical_entities()
            logger.info(f"Consolidation completed: {consolidation_results}")
        except Exception as exc:
            logger.warning(f"APOC consolidation failed, continuing without it: {exc}")
            consolidation_results = {
                "success": False,
                "error": str(exc),
                "message": "Consolidation skipped due to error"
            }
    
    # Return write results with optional consolidation info
    result = {
        "write_results": write_results,
        "triplets_written": len(write_results)
    }
    
    if consolidation_results:
        result["consolidation"] = consolidation_results
    
    return result







