"""Service for workspace management and multi-user collaboration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from ..core.settings import settings
from ..models.workspace import (
    Workspace,
    WorkspaceMember,
    WorkspacePermissions,
    WorkspaceStats,
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
    InviteMemberRequest,
    UpdateMemberRequest,
)
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class WorkspaceService:
    """Service for managing workspaces."""

    @staticmethod
    def create_workspace(user_id: str, user_email: str, request: CreateWorkspaceRequest) -> Workspace:
        """Create a new workspace."""
        workspace_id = str(uuid4())
        now = datetime.utcnow()

        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            # Create workspace node
            session.run(
                """
                CREATE (w:Workspace {
                    workspace_id: $workspace_id,
                    name: $name,
                    description: $description,
                    icon: $icon,
                    color: $color,
                    privacy: $privacy,
                    created_by: $user_id,
                    created_at: datetime($created_at),
                    updated_at: datetime($created_at),
                    archived: false
                })
                """,
                workspace_id=workspace_id,
                name=request.name,
                description=request.description,
                icon=request.icon,
                color=request.color,
                privacy=request.privacy,
                user_id=user_id,
                created_at=now.isoformat(),
            )

            # Add creator as owner (create User node if doesn't exist)
            session.run(
                """
                MERGE (u:User {user_id: $user_id})
                ON CREATE SET u.user_email = $user_email, u.created_at = datetime()
                WITH u
                MATCH (w:Workspace {workspace_id: $workspace_id})
                CREATE (u)-[:MEMBER_OF {
                    role: 'owner',
                    permissions: $permissions,
                    joined_at: datetime($joined_at)
                }]->(w)
                """,
                user_id=user_id,
                user_email=user_email,
                workspace_id=workspace_id,
                permissions=['view', 'add_documents', 'edit_relationships', 'invite_others', 'manage_workspace'],
                joined_at=now.isoformat(),
            )

        logger.info(f"Created workspace {workspace_id} for user {user_id}")

        # Return the created workspace
        return WorkspaceService.get_workspace(workspace_id, user_id)

    @staticmethod
    def get_workspace(workspace_id: str, user_id: str) -> Optional[Workspace]:
        """Get a workspace by ID."""
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (w:Workspace {workspace_id: $workspace_id})
                OPTIONAL MATCH (u:User)-[m:MEMBER_OF]->(w)
                WHERE u.user_id = $user_id
                RETURN w, m
                """,
                workspace_id=workspace_id,
                user_id=user_id,
            )

            record = result.single()
            if not record:
                return None

            w = record["w"]
            membership = record["m"]

            if not membership:
                # User is not a member
                return None

            # Get members
            members = WorkspaceService._get_workspace_members(workspace_id)

            # Get stats
            stats = WorkspaceService._get_workspace_stats(workspace_id)

            return Workspace(
                workspace_id=w["workspace_id"],
                name=w["name"],
                description=w.get("description"),
                icon=w.get("icon", "📊"),
                color=w.get("color", "#3B82F6"),
                privacy=w.get("privacy", "private"),
                created_by=w["created_by"],
                created_at=w["created_at"].to_native(),
                updated_at=w.get("updated_at").to_native() if w.get("updated_at") else None,
                archived=w.get("archived", False),
                members=members,
                stats=stats,
            )

    @staticmethod
    def list_user_workspaces(user_id: str, include_archived: bool = False) -> List[Workspace]:
        """List all workspaces for a user."""
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            query = """
            MATCH (u:User {user_id: $user_id})-[m:MEMBER_OF]->(w:Workspace)
            WHERE w.archived = $archived OR $include_archived = true
            RETURN w, m
            ORDER BY w.updated_at DESC
            """

            result = session.run(
                query,
                user_id=user_id,
                archived=False,
                include_archived=include_archived,
            )

            workspaces = []
            for record in result:
                w = record["w"]
                members = WorkspaceService._get_workspace_members(w["workspace_id"])
                stats = WorkspaceService._get_workspace_stats(w["workspace_id"])

                workspace = Workspace(
                    workspace_id=w["workspace_id"],
                    name=w["name"],
                    description=w.get("description"),
                    icon=w.get("icon", "📊"),
                    color=w.get("color", "#3B82F6"),
                    privacy=w.get("privacy", "private"),
                    created_by=w["created_by"],
                    created_at=w["created_at"].to_native(),
                    updated_at=w.get("updated_at").to_native() if w.get("updated_at") else None,
                    archived=w.get("archived", False),
                    members=members,
                    stats=stats,
                )
                workspaces.append(workspace)

            return workspaces

    @staticmethod
    def update_workspace(workspace_id: str, user_id: str, request: UpdateWorkspaceRequest) -> Optional[Workspace]:
        """Update a workspace."""
        # Check if user has permission
        if not WorkspaceService._user_has_permission(workspace_id, user_id, 'manage_workspace'):
            logger.warning(f"User {user_id} does not have permission to update workspace {workspace_id}")
            return None

        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.icon is not None:
            updates["icon"] = request.icon
        if request.color is not None:
            updates["color"] = request.color
        if request.privacy is not None:
            updates["privacy"] = request.privacy

        if not updates:
            return WorkspaceService.get_workspace(workspace_id, user_id)

        updates["updated_at"] = datetime.utcnow().isoformat()

        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            set_clause = ", ".join([f"w.{key} = ${key}" for key in updates.keys()])
            session.run(
                f"""
                MATCH (w:Workspace {{workspace_id: $workspace_id}})
                SET {set_clause}
                """,
                workspace_id=workspace_id,
                **updates,
            )

        logger.info(f"Updated workspace {workspace_id}")
        return WorkspaceService.get_workspace(workspace_id, user_id)

    @staticmethod
    def delete_workspace(workspace_id: str, user_id: str) -> bool:
        """Delete a workspace (only owner can delete)."""
        # Check if user is owner
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[m:MEMBER_OF]->(w:Workspace {workspace_id: $workspace_id})
                RETURN m.role as role
                """,
                user_id=user_id,
                workspace_id=workspace_id,
            )

            record = result.single()
            if not record or record["role"] != "owner":
                logger.warning(f"User {user_id} is not owner of workspace {workspace_id}")
                return False

            # Delete workspace and all relationships
            session.run(
                """
                MATCH (w:Workspace {workspace_id: $workspace_id})
                OPTIONAL MATCH (w)<-[r]-()
                DELETE r, w
                """,
                workspace_id=workspace_id,
            )

        logger.info(f"Deleted workspace {workspace_id}")
        return True

    @staticmethod
    def archive_workspace(workspace_id: str, user_id: str) -> bool:
        """Archive a workspace."""
        if not WorkspaceService._user_has_permission(workspace_id, user_id, 'manage_workspace'):
            return False

        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            session.run(
                """
                MATCH (w:Workspace {workspace_id: $workspace_id})
                SET w.archived = true, w.updated_at = datetime()
                """,
                workspace_id=workspace_id,
            )

        logger.info(f"Archived workspace {workspace_id}")
        return True

    @staticmethod
    def invite_member(workspace_id: str, inviter_id: str, request: InviteMemberRequest) -> bool:
        """Invite a member to a workspace."""
        # Check if inviter has permission
        if not WorkspaceService._user_has_permission(workspace_id, inviter_id, 'invite_others'):
            logger.warning(f"User {inviter_id} does not have permission to invite to workspace {workspace_id}")
            return False

        # Find user by email
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (u:User {user_email: $email})
                RETURN u.user_id as user_id
                """,
                email=request.user_email,
            )

            record = result.single()
            if not record:
                logger.warning(f"User with email {request.user_email} not found")
                return False

            user_id = record["user_id"]

            # Check if already a member
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[m:MEMBER_OF]->(w:Workspace {workspace_id: $workspace_id})
                RETURN m
                """,
                user_id=user_id,
                workspace_id=workspace_id,
            )

            if result.single():
                logger.warning(f"User {user_id} is already a member of workspace {workspace_id}")
                return False

            # Set default permissions based on role
            permissions = request.permissions
            if not permissions:
                if request.role == "owner":
                    permissions = WorkspacePermissions(
                        view=True,
                        add_documents=True,
                        edit_relationships=True,
                        invite_others=True,
                        manage_workspace=True,
                    )
                elif request.role == "editor":
                    permissions = WorkspacePermissions(
                        view=True,
                        add_documents=True,
                        edit_relationships=True,
                        invite_others=False,
                        manage_workspace=False,
                    )
                else:  # viewer
                    permissions = WorkspacePermissions(
                        view=True,
                        add_documents=False,
                        edit_relationships=False,
                        invite_others=False,
                        manage_workspace=False,
                    )

            # Add member
            session.run(
                """
                MATCH (u:User {user_id: $user_id})
                MATCH (w:Workspace {workspace_id: $workspace_id})
                CREATE (u)-[:MEMBER_OF {
                    role: $role,
                    permissions: $permissions,
                    joined_at: datetime()
                }]->(w)
                SET w.updated_at = datetime()
                """,
                user_id=user_id,
                workspace_id=workspace_id,
                role=request.role,
                permissions=permissions.dict(),
            )

        logger.info(f"Added user {user_id} to workspace {workspace_id}")
        return True

    @staticmethod
    def remove_member(workspace_id: str, remover_id: str, member_id: str) -> bool:
        """Remove a member from a workspace."""
        # Check if remover has permission
        if not WorkspaceService._user_has_permission(workspace_id, remover_id, 'invite_others'):
            logger.warning(f"User {remover_id} does not have permission to remove members from workspace {workspace_id}")
            return False

        # Cannot remove owner
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $member_id})-[m:MEMBER_OF]->(w:Workspace {workspace_id: $workspace_id})
                WHERE m.role <> 'owner'
                DELETE m
                SET w.updated_at = datetime()
                RETURN count(m) as removed
                """,
                member_id=member_id,
                workspace_id=workspace_id,
            )

            record = result.single()
            if record and record["removed"] > 0:
                logger.info(f"Removed user {member_id} from workspace {workspace_id}")
                return True

        return False

    @staticmethod
    def _get_workspace_members(workspace_id: str) -> List[WorkspaceMember]:
        """Get all members of a workspace."""
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (u:User)-[m:MEMBER_OF]->(w:Workspace {workspace_id: $workspace_id})
                RETURN u, m
                """,
                workspace_id=workspace_id,
            )

            members = []
            for record in result:
                u = record["u"]
                m = record["m"]

                # Parse permissions
                perms_dict = m.get("permissions", {})
                if isinstance(perms_dict, list):
                    # Old format: list of permission strings
                    permissions = WorkspacePermissions(
                        view='view' in perms_dict,
                        add_documents='add_documents' in perms_dict,
                        edit_relationships='edit_relationships' in perms_dict,
                        invite_others='invite_others' in perms_dict,
                        manage_workspace='manage_workspace' in perms_dict,
                    )
                else:
                    # New format: dict
                    permissions = WorkspacePermissions(**perms_dict)

                member = WorkspaceMember(
                    user_id=u["user_id"],
                    user_email=u.get("user_email", ""),
                    user_first_name=u.get("user_first_name"),
                    user_last_name=u.get("user_last_name"),
                    role=m["role"],
                    permissions=permissions,
                    joined_at=m["joined_at"].to_native(),
                    online=False,  # TODO: Implement presence
                )
                members.append(member)

            return members

    @staticmethod
    def _get_workspace_stats(workspace_id: str) -> WorkspaceStats:
        """Get statistics for a workspace."""
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (d:Document)-[:BELONGS_TO]->(w:Workspace {workspace_id: $workspace_id})
                OPTIONAL MATCH (d)<-[:EXTRACTED_FROM]-(e:Entity)
                OPTIONAL MATCH (e)-[r]->()
                WITH w, count(DISTINCT d) as doc_count, count(DISTINCT e) as entity_count, count(DISTINCT r) as rel_count
                OPTIONAL MATCH (u:User)-[:MEMBER_OF]->(w)
                RETURN doc_count, entity_count, rel_count, count(DISTINCT u) as member_count
                """,
                workspace_id=workspace_id,
            )

            record = result.single()
            if record:
                return WorkspaceStats(
                    document_count=record["doc_count"] or 0,
                    entity_count=record["entity_count"] or 0,
                    relationship_count=record["rel_count"] or 0,
                    member_count=record["member_count"] or 0,
                )

        return WorkspaceStats()

    @staticmethod
    def _user_has_permission(workspace_id: str, user_id: str, permission: str) -> bool:
        """Check if user has a specific permission in workspace."""
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[m:MEMBER_OF]->(w:Workspace {workspace_id: $workspace_id})
                RETURN m.permissions as permissions, m.role as role
                """,
                user_id=user_id,
                workspace_id=workspace_id,
            )

            record = result.single()
            if not record:
                return False

            # Owner has all permissions
            if record["role"] == "owner":
                return True

            perms = record["permissions"]
            if isinstance(perms, list):
                return permission in perms
            elif isinstance(perms, dict):
                return perms.get(permission, False)

        return False


# Global service instance
workspace_service = WorkspaceService()
