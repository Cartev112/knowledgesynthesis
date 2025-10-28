"""API routes for workspace management."""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List

from ..models.workspace import (
    Workspace,
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
    InviteMemberRequest,
    UpdateMemberRequest,
)
from ..models.user import User
from ..core.auth import get_current_user
from ..services.workspace_service import workspace_service
from ..services.neo4j_client import neo4j_client
from ..core.settings import settings

router = APIRouter()


@router.get("/workspaces", response_model=List[Workspace])
def list_workspaces(
    include_archived: bool = False,
    current_user: User = Depends(get_current_user)
):
    """List all workspaces for the current user."""
    try:
        workspaces = workspace_service.list_user_workspaces(
            user_id=current_user.user_id,
            include_archived=include_archived
        )
        return workspaces
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workspaces: {str(e)}")


@router.post("/workspaces", response_model=Workspace, status_code=201)
def create_workspace(
    request: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new workspace."""
    try:
        workspace = workspace_service.create_workspace(
            user_id=current_user.user_id,
            user_email=current_user.email,
            request=request,
            user_first_name=current_user.first_name,
            user_last_name=current_user.last_name
        )
        return workspace
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workspace: {str(e)}")


@router.get("/workspaces/global/stats")
def get_global_stats(current_user: User = Depends(get_current_user)):
    """Get global statistics across the entire database (not workspace-scoped)."""
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                // Total documents
                MATCH (d:Document)
                WITH count(d) AS total_docs
                
                // Total entities
                OPTIONAL MATCH (e:Entity)
                WITH total_docs, count(e) AS total_entities
                
                // Total relationships between entities (exclude system rels)
                OPTIONAL MATCH (e1:Entity)-[r]->(e2:Entity)
                WHERE type(r) <> 'BELONGS_TO' AND type(r) <> 'EXTRACTED_FROM'
                WITH total_docs, total_entities, count(r) AS total_rels
                
                // Count all workspaces (not filtered by membership)
                OPTIONAL MATCH (w:Workspace)
                RETURN total_docs, total_entities, total_rels, count(w) AS total_workspaces
                """
            )

            record = result.single()
            if record:
                return {
                    "document_count": record["total_docs"] or 0,
                    "entity_count": record["total_entities"] or 0,
                    "relationship_count": record["total_rels"] or 0,
                    "workspace_count": record["total_workspaces"] or 0
                }

            return {
                "document_count": 0,
                "entity_count": 0,
                "relationship_count": 0,
                "workspace_count": 0
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get global stats: {str(e)}")


@router.get("/workspaces/{workspace_id}", response_model=Workspace)
def get_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a workspace by ID."""
    workspace = workspace_service.get_workspace(
        workspace_id=workspace_id,
        user_id=current_user.user_id
    )
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or access denied")
    
    return workspace


@router.put("/workspaces/{workspace_id}", response_model=Workspace)
def update_workspace(
    workspace_id: str,
    request: UpdateWorkspaceRequest,
    current_user: User = Depends(get_current_user)
):
    """Update a workspace."""
    workspace = workspace_service.update_workspace(
        workspace_id=workspace_id,
        user_id=current_user.user_id,
        request=request
    )
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or permission denied")
    
    return workspace


@router.delete("/workspaces/{workspace_id}", status_code=204)
def delete_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a workspace (owner only)."""
    success = workspace_service.delete_workspace(
        workspace_id=workspace_id,
        user_id=current_user.user_id
    )
    
    if not success:
        raise HTTPException(status_code=403, detail="Permission denied or workspace not found")
    
    return None


@router.post("/workspaces/{workspace_id}/archive", status_code=204)
def archive_workspace(
    workspace_id: str,
    current_user: User = Depends(get_current_user)
):
    """Archive a workspace."""
    success = workspace_service.archive_workspace(
        workspace_id=workspace_id,
        user_id=current_user.user_id
    )
    
    if not success:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return None


@router.post("/workspaces/{workspace_id}/invite", status_code=201)
def invite_member(
    workspace_id: str,
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_user)
):
    """Invite a member to a workspace."""
    success = workspace_service.invite_member(
        workspace_id=workspace_id,
        inviter_id=current_user.user_id,
        request=request
    )
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to invite member")
    
    return {"message": "Member invited successfully"}


@router.delete("/workspaces/{workspace_id}/members/{member_id}", status_code=204)
def remove_member(
    workspace_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a member from a workspace."""
    success = workspace_service.remove_member(
        workspace_id=workspace_id,
        remover_id=current_user.user_id,
        member_id=member_id
    )
    
    if not success:
        raise HTTPException(status_code=403, detail="Permission denied or member not found")
    
    return None


@router.put("/workspaces/{workspace_id}/members/{member_id}", status_code=200)
def update_member(
    workspace_id: str,
    member_id: str,
    request: UpdateMemberRequest,
    current_user: User = Depends(get_current_user)
):
    """Update a member's role or permissions."""
    # TODO: Implement update member functionality
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.get("/workspaces/{workspace_id}/documents")
def get_workspace_documents(
    workspace_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all documents in a workspace."""
    try:
        documents = workspace_service.get_workspace_documents(
            workspace_id=workspace_id,
            user_id=current_user.user_id
        )
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")


@router.get("/workspaces/{workspace_id}/entities")
def get_workspace_entities(
    workspace_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all entities in a workspace."""
    try:
        entities = workspace_service.get_workspace_entities(
            workspace_id=workspace_id,
            user_id=current_user.user_id
        )
        return {"entities": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entities: {str(e)}")


@router.get("/workspaces/{workspace_id}/relationships")
def get_workspace_relationships(
    workspace_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all relationships in a workspace."""
    try:
        relationships = workspace_service.get_workspace_relationships(
            workspace_id=workspace_id,
            user_id=current_user.user_id
        )
        return {"relationships": relationships}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get relationships: {str(e)}")


@router.post("/sync-user", status_code=200)
def sync_user_data(current_user: User = Depends(get_current_user)):
    """Sync current user data to Neo4j User node."""
    try:
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            session.run(
                """
                MERGE (u:User {user_id: $user_id})
                SET u.user_email = $user_email,
                    u.user_first_name = $user_first_name,
                    u.user_last_name = $user_last_name
                """,
                user_id=current_user.user_id,
                user_email=current_user.email,
                user_first_name=current_user.first_name,
                user_last_name=current_user.last_name
            )
        return {"message": "User data synced successfully", "user": current_user}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync user: {str(e)}")
