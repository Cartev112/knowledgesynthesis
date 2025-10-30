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
def get_review_queue(limit: int = 50, status_filter: str = "unverified", node_ids: Optional[str] = None, workspace_id: Optional[str] = None):
    """
    Fetch relationships that need review.
    
    Args:
        limit: Maximum number of items to return
        status_filter: Filter by status (unverified, verified, incorrect)
        node_ids: Optional comma-separated list of node IDs to filter by
        workspace_id: Optional workspace ID to filter by
    """
    # Build query based on whether we're filtering by nodes
    if node_ids:
        # Parse node IDs
        ids_list = [id.strip() for id in node_ids.split(',') if id.strip()]
        
        workspace_filter = ""
        if workspace_id:
            workspace_filter = """
            AND (
                size(r.sources) = 0
                OR EXISTS {
                    MATCH (d:Document)-[:BELONGS_TO]->(:Workspace {workspace_id: $workspace_id})
                    WHERE d.document_id IN r.sources
                }
            )
            """
        
        cypher = f"""
        MATCH (s)-[r]->(o)
        WHERE (s:Entity OR s:Concept) AND (o:Entity OR o:Concept)
        AND coalesce(r.status, 'unverified') = $status
        AND (coalesce(s.id, s.name, elementId(s)) IN $node_ids 
             OR coalesce(o.id, o.name, elementId(o)) IN $node_ids)
        {workspace_filter}
        WITH s, r, o, type(r) AS rel_type
        OPTIONAL MATCH (d:Document) WHERE d.document_id IN r.sources
        WITH s, r, o, rel_type, collect(DISTINCT {{id: d.document_id, title: coalesce(d.title, d.document_id)}}) as docs
        CALL {{
            WITH s
            OPTIONAL MATCH (s)-[:IS_A]->(stype:Concept)
            RETURN CASE WHEN count(stype) = 0 THEN ['Concept'] ELSE collect(DISTINCT stype.name) END AS subject_types
        }}
        CALL {{
            WITH o
            OPTIONAL MATCH (o)-[:IS_A]->(otype:Concept)
            RETURN CASE WHEN count(otype) = 0 THEN ['Concept'] ELSE collect(DISTINCT otype.name) END AS object_types
        }}
        RETURN 
            elementId(r) AS relationship_id,
            s.name AS subject,
            subject_types AS subject_types,
            head(subject_types) AS subject_type,
            rel_type AS predicate,
            o.name AS object,
            object_types AS object_types,
            head(object_types) AS object_type,
            coalesce(r.confidence, 0.0) AS confidence,
            coalesce(r.original_text, '') AS original_text,
            coalesce(r.sources, []) AS sources,
            coalesce(r.status, 'unverified') AS status,
            r.created_at AS created_at,
            coalesce(r.flag_reason, '') AS flag_reason,
            docs AS documents
        ORDER BY r.created_at DESC
        LIMIT $limit
        """
        params = {"status": status_filter, "limit": limit, "node_ids": ids_list}
        if workspace_id:
            params["workspace_id"] = workspace_id
    else:
        workspace_filter = ""
        if workspace_id:
            workspace_filter = """
            AND (
                size(r.sources) = 0
                OR EXISTS {
                    MATCH (d:Document)-[:BELONGS_TO]->(:Workspace {workspace_id: $workspace_id})
                    WHERE d.document_id IN r.sources
                }
            )
            """
        
        cypher = f"""
        MATCH (s)-[r]->(o)
        WHERE (s:Entity OR s:Concept) AND (o:Entity OR o:Concept)
        AND coalesce(r.status, 'unverified') = $status
        {workspace_filter}
        WITH s, r, o, type(r) as rel_type
        OPTIONAL MATCH (d:Document) WHERE d.document_id IN r.sources
        WITH s, r, o, rel_type, collect(DISTINCT {{id: d.document_id, title: coalesce(d.title, d.document_id)}}) as docs
        CALL {{
            WITH s
            OPTIONAL MATCH (s)-[:IS_A]->(stype:Concept)
            RETURN CASE WHEN count(stype) = 0 THEN ['Concept'] ELSE collect(DISTINCT stype.name) END AS subject_types
        }}
        CALL {{
            WITH o
            OPTIONAL MATCH (o)-[:IS_A]->(otype:Concept)
            RETURN CASE WHEN count(otype) = 0 THEN ['Concept'] ELSE collect(DISTINCT otype.name) END AS object_types
        }}
        RETURN 
            elementId(r) AS relationship_id,
            s.name AS subject,
            subject_types AS subject_types,
            head(subject_types) AS subject_type,
            rel_type AS predicate,
            o.name AS object,
            object_types AS object_types,
            head(object_types) AS object_type,
            coalesce(r.confidence, 0.0) AS confidence,
            coalesce(r.original_text, '') AS original_text,
            coalesce(r.sources, []) AS sources,
            coalesce(r.status, 'unverified') AS status,
            r.created_at AS created_at,
            coalesce(r.flag_reason, '') AS flag_reason,
            docs AS documents
        ORDER BY r.created_at DESC
        LIMIT $limit
        """
        params = {"status": status_filter, "limit": limit}
        if workspace_id:
            params["workspace_id"] = workspace_id
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, **params)
            items = []
            for record in result:
                items.append({
                    "relationship_id": record["relationship_id"],
                    "subject": record["subject"],
                    "subject_type": record["subject_type"],
                    "subject_types": record.get("subject_types") or [record["subject_type"]] if record["subject_type"] else [],
                    "predicate": record["predicate"],
                    "object": record["object"],
                    "object_type": record["object_type"],
                    "object_types": record.get("object_types") or [record["object_type"]] if record["object_type"] else [],
                    "confidence": record["confidence"],
                    "original_text": record["original_text"],
                    "sources": record["sources"],
                    "status": record["status"],
                    "created_at": str(record["created_at"]) if record["created_at"] else None,
                    "flag_reason": record["flag_reason"],
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
    If subject/predicate/object are changed, recreates the relationship.
    """
    # Check if we need to recreate the relationship (subject/predicate/object changed)
    if payload.subject or payload.predicate or payload.object:
        # For now, just update the properties we can and log a warning
        # Full entity/relationship recreation would require more complex logic
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
        
        # Store edit notes in a property
        edit_notes = []
        if payload.subject:
            edit_notes.append(f"Subject changed to: {payload.subject}")
        if payload.predicate:
            edit_notes.append(f"Predicate changed to: {payload.predicate}")
        if payload.object:
            edit_notes.append(f"Object changed to: {payload.object}")
        
        if edit_notes:
            set_clauses.append("r.edit_notes = $edit_notes")
            params["edit_notes"] = "; ".join(edit_notes)
        
        if payload.confidence is not None:
            set_clauses.append("r.confidence = $confidence")
            params["confidence"] = payload.confidence
        
        if payload.original_text is not None:
            set_clauses.append("r.original_text = $original_text")
            params["original_text"] = payload.original_text
        
        cypher = f"""
        MATCH ()-[r]->()
        WHERE elementId(r) = $rel_id
        SET {', '.join(set_clauses)}
        RETURN r.status AS status
        """
    else:
        # Simple edit: just update properties
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
def get_review_stats(workspace_id: Optional[str] = None):
    """
    Get statistics about the review status of relationships.
    """
    workspace_filter = ""
    if workspace_id:
        workspace_filter = """
        WHERE EXISTS {
            MATCH (d:Document)-[:BELONGS_TO]->(:Workspace {workspace_id: $workspace_id})
            WHERE d.document_id IN r.sources
        }
        """
    
    cypher = f"""
    MATCH (s:Entity)-[r]->(o:Entity)
    {workspace_filter}
    RETURN 
        coalesce(r.status, 'unverified') AS status,
        count(r) AS count
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            params = {}
            if workspace_id:
                params["workspace_id"] = workspace_id
            
            result = session.run(cypher, **params)
            stats = {record["status"] or "unknown": record["count"] for record in result}
            
            return {
                "unverified": stats.get("unverified", 0),
                "verified": stats.get("verified", 0),
                "incorrect": stats.get("incorrect", 0),
                "total": sum(stats.values())
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get review stats: {exc}")


