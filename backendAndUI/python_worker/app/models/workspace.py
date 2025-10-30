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
    view_config: Optional[WorkspaceViewConfig] = Field(default=None, description="View/filter configuration for this workspace")


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
    view_config: Optional[WorkspaceViewConfig] = None


class AddDocumentsToWorkspaceRequest(BaseModel):
    """Request to add existing documents to a workspace."""
    document_ids: List[str] = Field(..., min_items=1, description="Document IDs to add to workspace")


class RemoveDocumentsFromWorkspaceRequest(BaseModel):
    """Request to remove documents from a workspace."""
    document_ids: List[str] = Field(..., min_items=1, description="Document IDs to remove from workspace")


class InviteMemberRequest(BaseModel):
    """Request to invite a member to a workspace."""
    user_email: str
    role: str = "viewer"
    permissions: Optional[WorkspacePermissions] = None


class UpdateMemberRequest(BaseModel):
    """Request to update a member's role or permissions."""
    role: Optional[str] = None
    permissions: Optional[WorkspacePermissions] = None


class WorkspaceViewConfig(BaseModel):
    """Configuration for workspace view/filter settings."""
    # Document filters
    included_document_ids: Optional[List[str]] = Field(default=None, description="Specific documents to include")
    excluded_document_ids: Optional[List[str]] = Field(default=None, description="Specific documents to exclude")
    
    # Entity filters
    included_entity_types: Optional[List[str]] = Field(default=None, description="Entity types to show")
    excluded_entity_types: Optional[List[str]] = Field(default=None, description="Entity types to hide")
    
    # Relationship filters
    included_relationship_types: Optional[List[str]] = Field(default=None, description="Relationship types to show")
    excluded_relationship_types: Optional[List[str]] = Field(default=None, description="Relationship types to hide (e.g., IS_A)")
    show_is_a_relationships: bool = Field(default=True, description="Show ontological IS_A relationships")
    
    # Significance filters
    min_node_significance: Optional[int] = Field(default=None, ge=1, le=5, description="Minimum node significance (1-5)")
    min_relationship_significance: Optional[int] = Field(default=None, ge=1, le=5, description="Minimum relationship significance (1-5)")
    
    # Visualization settings
    layout_algorithm: str = Field(default="cose", description="Graph layout algorithm")
    node_color_scheme: str = Field(default="by-type", description="Node coloring scheme")
    node_size_scheme: str = Field(default="by-significance", description="Node sizing scheme")
    label_display_mode: str = Field(default="hover", description="Label display mode")


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
