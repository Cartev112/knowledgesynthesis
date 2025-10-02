"""Review and verification endpoints for expert curation."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ..services.neo4j_client import neo4j_client
from ..core.settings import settings


router = APIRouter()


class ReviewConfirmRequest(BaseModel):
    """Request to confirm a relationship."""
    reviewer_id: Optional[str] = None
    reviewer_first_name: Optional[str] = None
    reviewer_last_name: Optional[str] = None


class ReviewEditRequest(BaseModel):
    """Request to edit a relationship."""
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object: Optional[str] = None
    confidence: Optional[float] = None
    original_text: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewer_first_name: Optional[str] = None
    reviewer_last_name: Optional[str] = None


class ReviewFlagRequest(BaseModel):
    """Request to flag a relationship as incorrect."""
    reason: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewer_first_name: Optional[str] = None
    reviewer_last_name: Optional[str] = None


@router.get("/queue")
def get_review_queue(limit: int = 50, status_filter: str = "unverified"):
    """
    Fetch relationships that need review.
    
    Args:
        limit: Maximum number of items to return
        status_filter: Filter by status (unverified, verified, incorrect)
    """
    cypher = """
    MATCH (s:Entity)-[r]->(o:Entity)
    WHERE coalesce(r.status, 'unverified') = $status
    WITH s, r, o, type(r) as rel_type
    OPTIONAL MATCH (d:Document) WHERE d.document_id IN r.sources
    WITH s, r, o, rel_type, collect(DISTINCT {id: d.document_id, title: coalesce(d.title, d.document_id)}) as docs
    RETURN 
        elementId(r) AS relationship_id,
        s.name AS subject,
        s.type AS subject_type,
        rel_type AS predicate,
        o.name AS object,
        o.type AS object_type,
        r.confidence AS confidence,
        r.original_text AS original_text,
        r.sources AS sources,
        coalesce(r.status, 'unverified') AS status,
        r.created_at AS created_at,
        docs AS documents
    ORDER BY r.created_at DESC
    LIMIT $limit
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, status=status_filter, limit=limit)
            items = []
            for record in result:
                items.append({
                    "relationship_id": record["relationship_id"],
                    "subject": record["subject"],
                    "subject_type": record["subject_type"],
                    "predicate": record["predicate"],
                    "object": record["object"],
                    "object_type": record["object_type"],
                    "confidence": record["confidence"],
                    "original_text": record["original_text"],
                    "sources": record["sources"],
                    "status": record["status"],
                    "created_at": str(record["created_at"]) if record["created_at"] else None,
                    "documents": [d for d in record["documents"] if d.get("id")],
                })
            return {"items": items, "count": len(items)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to fetch review queue: {exc}")


@router.post("/{relationship_id}/confirm")
def confirm_relationship(relationship_id: str, payload: ReviewConfirmRequest):
    """
    Mark a relationship as verified/confirmed.
    """
    cypher = """
    MATCH ()-[r]->()
    WHERE elementId(r) = $rel_id
    SET r.status = 'verified',
        r.reviewed_at = datetime(),
        r.reviewed_by = $reviewer_id,
        r.reviewed_by_first_name = $reviewer_first_name,
        r.reviewed_by_last_name = $reviewer_last_name
    RETURN r.status AS status
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                cypher,
                rel_id=relationship_id,
                reviewer_id=payload.reviewer_id or "system",
                reviewer_first_name=payload.reviewer_first_name or "",
                reviewer_last_name=payload.reviewer_last_name or ""
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Relationship not found")
            
            return {"status": "confirmed", "new_status": record["status"]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to confirm relationship: {exc}")


@router.post("/{relationship_id}/edit")
def edit_relationship(relationship_id: str, payload: ReviewEditRequest):
    """
    Edit a relationship and mark it as verified.
    """
    # Build dynamic SET clause based on provided fields
    set_clauses = [
        "r.status = 'verified'", 
        "r.reviewed_at = datetime()", 
        "r.reviewed_by = $reviewer_id",
        "r.reviewed_by_first_name = $reviewer_first_name",
        "r.reviewed_by_last_name = $reviewer_last_name"
    ]
    params = {
        "rel_id": relationship_id,
        "reviewer_id": payload.reviewer_id or "system",
        "reviewer_first_name": payload.reviewer_first_name or "",
        "reviewer_last_name": payload.reviewer_last_name or ""
    }
    
    if payload.confidence is not None:
        set_clauses.append("r.confidence = $confidence")
        params["confidence"] = payload.confidence
    
    if payload.original_text is not None:
        set_clauses.append("r.original_text = $original_text")
        params["original_text"] = payload.original_text
    
    # Note: Editing subject/predicate/object requires recreating the relationship
    # This is a more complex operation that we'll handle separately if needed
    if payload.subject or payload.predicate or payload.object:
        raise HTTPException(
            status_code=400,
            detail="Editing subject, predicate, or object not yet supported. Please flag as incorrect and create a new extraction."
        )
    
    cypher = f"""
    MATCH ()-[r]->()
    WHERE elementId(r) = $rel_id
    SET {', '.join(set_clauses)}
    RETURN r.status AS status
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, **params)
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Relationship not found")
            
            return {"status": "edited", "new_status": record["status"]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to edit relationship: {exc}")


@router.post("/{relationship_id}/flag")
def flag_relationship(relationship_id: str, payload: ReviewFlagRequest):
    """
    Flag a relationship as incorrect.
    """
    cypher = """
    MATCH ()-[r]->()
    WHERE elementId(r) = $rel_id
    SET r.status = 'incorrect',
        r.reviewed_at = datetime(),
        r.reviewed_by = $reviewer_id,
        r.reviewed_by_first_name = $reviewer_first_name,
        r.reviewed_by_last_name = $reviewer_last_name,
        r.flag_reason = $reason
    RETURN r.status AS status
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                cypher,
                rel_id=relationship_id,
                reviewer_id=payload.reviewer_id or "system",
                reviewer_first_name=payload.reviewer_first_name or "",
                reviewer_last_name=payload.reviewer_last_name or "",
                reason=payload.reason or ""
            )
            record = result.single()
            if not record:
                raise HTTPException(status_code=404, detail="Relationship not found")
            
            return {"status": "flagged", "new_status": record["status"]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to flag relationship: {exc}")


@router.get("/stats")
def get_review_stats():
    """
    Get statistics about the review status of relationships.
    """
    cypher = """
    MATCH (s:Entity)-[r]->(o:Entity)
    RETURN 
        coalesce(r.status, 'unverified') AS status,
        count(r) AS count
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher)
            stats = {record["status"] or "unknown": record["count"] for record in result}
            
            return {
                "unverified": stats.get("unverified", 0),
                "verified": stats.get("verified", 0),
                "incorrect": stats.get("incorrect", 0),
                "total": sum(stats.values())
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get review stats: {exc}")

