"""Migration endpoints for fixing data issues."""
from fastapi import APIRouter, HTTPException, Depends
from ..core.auth import get_current_user
from ..models.user import User
from ..services.neo4j_client import neo4j_client
from ..core.settings import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/migrate/link-entities-to-workspaces")
def link_entities_to_workspaces(current_user: User = Depends(get_current_user)):
    """
    Backfill BELONGS_TO relationships for entities.
    Links all entities to workspaces based on their EXTRACTED_FROM -> Document -> BELONGS_TO -> Workspace path.
    """
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (e:Entity)-[:EXTRACTED_FROM]->(d:Document)-[:BELONGS_TO]->(w:Workspace)
                MERGE (e)-[:BELONGS_TO]->(w)
                RETURN count(DISTINCT e) as entities_linked, count(DISTINCT w) as workspaces_affected
                """
            )
            
            record = result.single()
            if record:
                return {
                    "success": True,
                    "entities_linked": record["entities_linked"],
                    "workspaces_affected": record["workspaces_affected"],
                    "message": f"Successfully linked {record['entities_linked']} entities to {record['workspaces_affected']} workspaces"
                }
            
            return {
                "success": True,
                "entities_linked": 0,
                "workspaces_affected": 0,
                "message": "No entities to link"
            }
            
    except Exception as e:
        logger.error(f"Failed to link entities to workspaces: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")


@router.get("/migrate/check-workspace-links")
def check_workspace_links():
    """
    Check the status of workspace linking.
    Returns counts of documents, entities with and without workspace links.
    No authentication required for checking status.
    """
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (d:Document)
                OPTIONAL MATCH (d)-[:BELONGS_TO]->(w:Workspace)
                WITH count(d) as total_docs, count(w) as linked_docs
                
                MATCH (e:Entity)
                OPTIONAL MATCH (e)-[:BELONGS_TO]->(w2:Workspace)
                WITH total_docs, linked_docs, count(e) as total_entities, count(w2) as linked_entities
                
                RETURN total_docs, linked_docs, total_entities, linked_entities
                """
            )
            
            record = result.single()
            if record:
                return {
                    "documents": {
                        "total": record["total_docs"],
                        "linked_to_workspace": record["linked_docs"],
                        "unlinked": record["total_docs"] - record["linked_docs"]
                    },
                    "entities": {
                        "total": record["total_entities"],
                        "linked_to_workspace": record["linked_entities"],
                        "unlinked": record["total_entities"] - record["linked_entities"]
                    }
                }
            
            return {
                "documents": {"total": 0, "linked_to_workspace": 0, "unlinked": 0},
                "entities": {"total": 0, "linked_to_workspace": 0, "unlinked": 0}
            }
            
    except Exception as e:
        logger.error(f"Failed to check workspace links: {e}")
        raise HTTPException(status_code=500, detail=f"Check failed: {str(e)}")
