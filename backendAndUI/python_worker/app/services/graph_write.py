from __future__ import annotations

from typing import Dict, Iterable, Optional, List
import logging
import hashlib

from .neo4j_client import neo4j_client
from .entity_consolidation import consolidate_identical_entities
from ..models.triplet import Triplet
from ..core.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_OWNER_PERMISSIONS = ["view", "add_documents", "edit_relationships", "invite_others", "manage_workspace"]


MERGE_TRIPLET_CYPHER = """
MERGE (s:Entity:Concept {name: $s_name})
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
WITH s
FOREACH (stype IN $s_types |
    MERGE (st:Entity:Concept {name: stype})
    MERGE (s)-[:IS_A]->(st)
)

MERGE (o:Entity:Concept {name: $o_name})
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
WITH s, o
FOREACH (otype IN $o_types |
    MERGE (ot:Entity:Concept {name: otype})
    MERGE (o)-[:IS_A]->(ot)
)
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
        "s_types": triplet.subject_types,
        "o_name": triplet.object,
        "o_types": triplet.object_types,
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


def write_triplets(triplets: Iterable[Triplet], document_id: str, document_title: Optional[str] = None, user_id: Optional[str] = None, user_first_name: Optional[str] = None, user_last_name: Optional[str] = None, workspace_id: Optional[str] = None, workspace_metadata: Optional[Dict[str, object]] = None, consolidate_entities: bool = True) -> list[dict]:
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
        workspace_metadata: Optional workspace metadata to ensure node integrity
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
            workspace_info = workspace_metadata or {}
            owner_info = workspace_info.get("owner") or {}

            owner_permissions = workspace_info.get("owner_permissions") or DEFAULT_OWNER_PERMISSIONS
            workspace_created_by = workspace_info.get("created_by") or user_id or "anonymous"
            workspace_created_at = workspace_info.get("created_at")

            workspace_params = {
                "workspace_id": workspace_id,
                "workspace_name": workspace_info.get("name"),
                "workspace_description": workspace_info.get("description"),
                "workspace_icon": workspace_info.get("icon"),
                "default_workspace_icon": workspace_info.get("icon") or "\U0001F4C2",
                "workspace_color": workspace_info.get("color"),
                "default_workspace_color": workspace_info.get("color") or "#3B82F6",
                "workspace_privacy": workspace_info.get("privacy"),
                "workspace_created_by": workspace_created_by,
                "workspace_created_at": workspace_created_at,
                "owner_id": owner_info.get("user_id") or workspace_created_by,
                "owner_email": owner_info.get("email"),
                "owner_first_name": owner_info.get("first_name"),
                "owner_last_name": owner_info.get("last_name"),
                "owner_permissions": owner_permissions,
                "user_id": user_id or "anonymous",
            }

            tx.run(
                """
                MERGE (w:Workspace {workspace_id: $workspace_id})
                ON CREATE SET
                    w.name = coalesce($workspace_name, $workspace_id),
                    w.description = $workspace_description,
                    w.icon = coalesce($workspace_icon, $default_workspace_icon),
                    w.color = coalesce($workspace_color, $default_workspace_color),
                    w.privacy = coalesce($workspace_privacy, 'private'),
                    w.created_by = $workspace_created_by,
                    w.created_at = CASE
                        WHEN $workspace_created_at IS NOT NULL THEN datetime($workspace_created_at)
                        ELSE datetime()
                    END,
                    w.updated_at = datetime(),
                    w.archived = false
                ON MATCH SET
                    w.name = CASE WHEN $workspace_name IS NOT NULL THEN $workspace_name ELSE w.name END,
                    w.description = CASE WHEN $workspace_description IS NOT NULL THEN $workspace_description ELSE w.description END,
                    w.icon = CASE WHEN $workspace_icon IS NOT NULL THEN $workspace_icon ELSE w.icon END,
                    w.color = CASE WHEN $workspace_color IS NOT NULL THEN $workspace_color ELSE w.color END,
                    w.privacy = CASE WHEN $workspace_privacy IS NOT NULL THEN $workspace_privacy ELSE w.privacy END,
                    w.updated_at = datetime()
                """,
                workspace_params
            )

            owner_id = workspace_params["owner_id"]
            if owner_id:
                tx.run(
                    """
                    MERGE (owner:User {user_id: $owner_id})
                    SET owner.user_email = CASE WHEN $owner_email IS NOT NULL THEN $owner_email ELSE owner.user_email END,
                        owner.user_first_name = CASE WHEN $owner_first_name IS NOT NULL AND $owner_first_name <> '' THEN $owner_first_name ELSE owner.user_first_name END,
                        owner.user_last_name = CASE WHEN $owner_last_name IS NOT NULL AND $owner_last_name <> '' THEN $owner_last_name ELSE owner.user_last_name END
                    WITH owner
                    MATCH (w:Workspace {workspace_id: $workspace_id})
                    MERGE (owner)-[membership:MEMBER_OF]->(w)
                    ON CREATE SET
                        membership.role = 'owner',
                        membership.permissions = $owner_permissions,
                        membership.joined_at = datetime()
                    """,
                    {
                        "workspace_id": workspace_id,
                        "owner_id": owner_id,
                        "owner_email": workspace_params["owner_email"],
                        "owner_first_name": workspace_params["owner_first_name"],
                        "owner_last_name": workspace_params["owner_last_name"],
                        "owner_permissions": owner_permissions,
                    }
                )

            tx.run(
                """
                MATCH (d:Document {document_id: $document_id})
                MATCH (w:Workspace {workspace_id: $workspace_id})
                MERGE (d)-[:BELONGS_TO]->(w)
                """,
                document_id=document_id,
                workspace_id=workspace_id
            )

            # Also link all entities extracted from this document to the workspace
            tx.run(
                """
                MATCH (d:Document {document_id: $document_id})
                MATCH (w:Workspace {workspace_id: $workspace_id})
                MATCH (e:Entity)-[:EXTRACTED_FROM]->(d)
                MERGE (e)-[:BELONGS_TO]->(w)
                """,
                document_id=document_id,
                workspace_id=workspace_id
            )

            logger.info(f"Associated document {document_id} and its entities with workspace {workspace_id}")
        
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


def _embed_triplet(subject: str, predicate: str, object: str, original_text: str) -> List[float]:
    """
    Create embedding for a triplet combining structured and unstructured information.
    Format: "{subject} {predicate} {object}. Context: {original_text}"
    """
    if settings.openai_dry_run or not settings.openai_api_key:
        # Dry run mode
        dim = settings.openai_embedding_dim
        combined = f"{subject}{predicate}{object}{original_text}"
        return [(hash(combined + str(i)) % 1000) / 1000.0 for i in range(dim)]
    
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Combine structured triplet with contextual evidence (truncate text to avoid token limits)
    triplet_text = f"{subject} {predicate} {object}. Context: {original_text[:500]}"
    
    resp = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=[triplet_text]
    )
    return resp.data[0].embedding


def write_triplet_with_embedding(
    subject: str,
    predicate: str,
    object: str,
    original_text: str,
    sources: List[str],
    page_number: Optional[int] = None,
    confidence: float = 1.0,
    status: str = "unverified",
    user_id: Optional[str] = None,
    subject_types: Optional[List[str]] = None,
    object_types: Optional[List[str]] = None
) -> str:
    """
    Write a triplet node with embedding to Neo4j.
    Also creates the traditional relationship for backward compatibility.
    
    Returns: triplet_id
    """
    subject_types = [t.strip() for t in (subject_types or ["Concept"]) if isinstance(t, str) and t.strip()]
    object_types = [t.strip() for t in (object_types or ["Concept"]) if isinstance(t, str) and t.strip()]
    if not subject_types:
        subject_types = ["Concept"]
    if not object_types:
        object_types = ["Concept"]

    # Generate embedding
    embedding = _embed_triplet(subject, predicate, object, original_text)
    
    # Create unique ID
    triplet_id = hashlib.md5(
        f"{subject}|{predicate}|{object}|{sources[0]}".encode()
    ).hexdigest()
    
    # Normalize predicate for relationship type
    rel_type = predicate.strip().upper().replace(" ", "_")
    
    cypher = f"""
    // Create or merge entities (existing logic)
    MERGE (s:Entity:Concept {{name: $subject}})
    ON CREATE SET s.created_at = datetime()
    WITH s
    FOREACH (stype IN $subject_types |
        MERGE (st:Entity:Concept {{name: stype}})
        MERGE (s)-[:IS_A]->(st)
    )
    
    MERGE (o:Entity:Concept {{name: $object}})
    ON CREATE SET o.created_at = datetime()
    WITH s, o
    FOREACH (otype IN $object_types |
        MERGE (ot:Entity:Concept {{name: otype}})
        MERGE (o)-[:IS_A]->(ot)
    )
    
    // Create traditional relationship (for backward compatibility)
    MERGE (s)-[r:{rel_type}]->(o)
    ON CREATE SET 
        r.original_text = $original_text,
        r.sources = $sources,
        r.page_number = $page_number,
        r.confidence = $confidence,
        r.status = $status,
        r.created_at = datetime(),
        r.created_by = $user_id
    ON MATCH SET
        r.sources = CASE
            WHEN r.sources IS NULL THEN $sources
            ELSE r.sources + [x IN $sources WHERE NOT x IN r.sources]
        END
    
    // Create Triplet node with embedding
    MERGE (t:Triplet {{id: $triplet_id}})
    ON CREATE SET 
        t.subject = $subject,
        t.predicate = $predicate,
        t.object = $object,
        t.original_text = $original_text,
        t.embedding = $embedding,
        t.sources = $sources,
        t.page_number = $page_number,
        t.confidence = $confidence,
        t.status = $status,
        t.created_at = datetime(),
        t.embedding_model = $embedding_model
    ON MATCH SET
        t.sources = t.sources + [x IN $sources WHERE NOT x IN t.sources]
    
    // Link triplet to entities
    MERGE (t)-[:ABOUT_SUBJECT]->(s)
    MERGE (t)-[:ABOUT_OBJECT]->(o)
    
    // Link triplet to documents
    WITH t, $sources as doc_ids
    UNWIND doc_ids as doc_id
    MERGE (d:Document {{document_id: doc_id}})
    MERGE (t)-[:FROM_DOCUMENT]->(d)
    
    RETURN t.id as triplet_id
    """
    
    with neo4j_client._driver.session(database=settings.neo4j_database) as session:
        result = session.run(
            cypher,
            subject=subject,
            predicate=predicate,
            object=object,
            original_text=original_text,
            sources=sources,
            page_number=page_number,
            confidence=confidence,
            status=status,
            embedding=embedding,
            triplet_id=triplet_id,
            user_id=user_id or "anonymous",
            subject_types=subject_types,
            object_types=object_types,
            embedding_model=settings.openai_embedding_model
        )
        record = result.single()
        logger.info(f"Created triplet node: {triplet_id} ({subject} {predicate} {object})")
        return record["triplet_id"] if record else triplet_id
