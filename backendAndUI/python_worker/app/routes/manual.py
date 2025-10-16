"""Manual annotation endpoints for expert-created relationships."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..services.neo4j_client import neo4j_client
from ..core.settings import settings


router = APIRouter()


class ManualRelationshipRequest(BaseModel):
    """Request to create a manual relationship."""
    subject_id: str
    subject_name: str
    object_id: str
    object_name: str
    relation: str
    evidence: str
    confidence: float = 0.9
    created_by: Optional[str] = None
    created_by_first_name: Optional[str] = None
    created_by_last_name: Optional[str] = None


@router.post("/relationship")
def create_manual_relationship(payload: ManualRelationshipRequest):
    """
    Create a manually annotated relationship between two entities.
    
    This allows domain experts to add relationships that the AI missed.
    The relationship is marked as 'verified' since it's expert-created.
    """
    # Normalize relation type
    relation_type = payload.relation.upper().replace(' ', '_').replace('-', '_')
    
    cypher = """
    // Find or get the subject and object nodes by ID
    MATCH (s:Entity)
    WHERE coalesce(s.id, s.name, elementId(s)) = $subject_id
    
    MATCH (o:Entity)
    WHERE coalesce(o.id, o.name, elementId(o)) = $object_id
    
    // Create the manual relationship
    CREATE (s)-[r:MANUAL_ANNOTATION {
        relation: $relation,
        original_text: $evidence,
        confidence: $confidence,
        status: 'verified',
        polarity: 'positive',
        significance: 5,
        sources: ['manual_annotation'],
        created_at: datetime(),
        created_by: $created_by,
        created_by_first_name: $created_by_first_name,
        created_by_last_name: $created_by_last_name,
        is_manual: true
    }]->(o)
    
    RETURN elementId(r) as relationship_id, 
           s.name as subject_name, 
           o.name as object_name,
           $relation as relation_type
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                cypher,
                subject_id=payload.subject_id,
                object_id=payload.object_id,
                relation=payload.relation,
                evidence=payload.evidence,
                confidence=payload.confidence,
                created_by=payload.created_by or "expert-user",
                created_by_first_name=payload.created_by_first_name or "",
                created_by_last_name=payload.created_by_last_name or ""
            )
            record = result.single()
            
            if not record:
                raise HTTPException(
                    status_code=404, 
                    detail="Could not find one or both entities. Please ensure they exist in the graph."
                )
            
            return {
                "status": "created",
                "relationship_id": record["relationship_id"],
                "subject": record["subject_name"],
                "relation": record["relation_type"],
                "object": record["object_name"],
                "message": "Manual relationship created successfully"
            }
            
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create manual relationship: {exc}"
        )


@router.get("/relationships")
def get_manual_relationships(limit: int = 100):
    """
    Get all manually created relationships.
    """
    cypher = """
    MATCH (s:Entity)-[r:MANUAL_ANNOTATION]->(o:Entity)
    RETURN 
        elementId(r) as id,
        s.name as subject,
        r.relation as relation,
        o.name as object,
        r.confidence as confidence,
        r.original_text as evidence,
        r.created_at as created_at,
        r.created_by as created_by,
        r.created_by_first_name as created_by_first_name,
        r.created_by_last_name as created_by_last_name
    ORDER BY r.created_at DESC
    LIMIT $limit
    """
    
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(cypher, limit=limit)
            relationships = []
            
            for record in result:
                relationships.append({
                    "id": record["id"],
                    "subject": record["subject"],
                    "relation": record["relation"],
                    "object": record["object"],
                    "confidence": record["confidence"],
                    "evidence": record["evidence"],
                    "created_at": str(record["created_at"]) if record["created_at"] else None,
                    "created_by": record["created_by"],
                    "created_by_name": f"{record['created_by_first_name']} {record['created_by_last_name']}".strip()
                })
            
            return {
                "relationships": relationships,
                "count": len(relationships)
            }
            
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch manual relationships: {exc}"
        )
