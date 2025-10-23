"""Workspace data models for multi-user collaboration."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WorkspacePermissions(BaseModel):
    """Permissions for a workspace member."""
    view: bool = True
    add_documents: bool = False
    edit_relationships: bool = False
    invite_others: bool = False
    manage_workspace: bool = False


class WorkspaceMember(BaseModel):
    """A member of a workspace."""
    user_id: str
    user_email: str
    user_first_name: Optional[str] = None
    user_last_name: Optional[str] = None
    role: str = Field(..., description="owner, editor, or viewer")
    permissions: WorkspacePermissions
    joined_at: datetime
    online: bool = False


class WorkspaceStats(BaseModel):
    """Statistics for a workspace."""
    document_count: int = 0
    entity_count: int = 0
    relationship_count: int = 0
    member_count: int = 0
    last_activity: Optional[datetime] = None


class Workspace(BaseModel):
    """A workspace containing related documents and knowledge."""
    workspace_id: str
    name: str
    description: Optional[str] = None
    icon: str = "📊"
    color: str = "#3B82F6"
    privacy: str = Field(default="private", description="private, organization, or public")
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    archived: bool = False
    members: List[WorkspaceMember] = []
    stats: Optional[WorkspaceStats] = None


class CreateWorkspaceRequest(BaseModel):
    """Request to create a new workspace."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: str = "📊"
    color: str = "#3B82F6"
    privacy: str = "private"


class UpdateWorkspaceRequest(BaseModel):
    """Request to update a workspace."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    icon: Optional[str] = None
    color: Optional[str] = None
    privacy: Optional[str] = None


class InviteMemberRequest(BaseModel):
    """Request to invite a member to a workspace."""
    user_email: str
    role: str = "viewer"
    permissions: Optional[WorkspacePermissions] = None


class UpdateMemberRequest(BaseModel):
    """Request to update a member's role or permissions."""
    role: Optional[str] = None
    permissions: Optional[WorkspacePermissions] = None


class GraphFilter(BaseModel):
    """Filters for graph queries."""
    workspace_id: Optional[str] = None
    view_mode: str = Field(default="workspace", description="my_content, workspace, collaborative, or global")
    user_ids: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    date_range: Optional[dict] = None
    significance_range: Optional[dict] = None
    document_ids: Optional[List[str]] = None
    limit: int = 1000
