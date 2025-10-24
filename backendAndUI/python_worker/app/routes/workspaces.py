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
