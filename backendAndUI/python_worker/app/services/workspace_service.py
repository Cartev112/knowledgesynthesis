"""Service for workspace management and multi-user collaboration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from ..core.settings import settings
from ..models.workspace import (
    Workspace,
    WorkspaceMember,
    WorkspacePermissions,
    WorkspaceStats,
    WorkspaceViewConfig,
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
    InviteMemberRequest,
    UpdateMemberRequest,
    AddDocumentsToWorkspaceRequest,
    RemoveDocumentsFromWorkspaceRequest,
)
from .neo4j_client import neo4j_client

logger = logging.getLogger(__name__)

COLLABORATIVE_PRIVACIES = {"public", "shared", "organization"}
SHARED_OPEN_WRITE_PERMISSIONS = {"view", "add_documents", "edit_relationships"}
OWNER_PERMISSIONS = ["view", "add_documents", "edit_relationships", "invite_others", "manage_workspace"]


class WorkspaceService:
    """Service for managing workspaces."""

    @staticmethod
    def create_workspace(user_id: str, user_email: str, request: CreateWorkspaceRequest, user_first_name: str = None, user_last_name: str = None) -> Workspace:
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
                ON CREATE SET u.user_email = $user_email, u.user_first_name = $user_first_name, u.user_last_name = $user_last_name, u.created_at = datetime()
                ON MATCH SET 
                    u.user_email = $user_email,
                    u.user_first_name = CASE WHEN $user_first_name <> '' THEN $user_first_name ELSE u.user_first_name END,
                    u.user_last_name = CASE WHEN $user_last_name <> '' THEN $user_last_name ELSE u.user_last_name END
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
                user_first_name=user_first_name,
                user_last_name=user_last_name,
                workspace_id=workspace_id,
                permissions=OWNER_PERMISSIONS,
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
            privacy = w.get("privacy", "private")

            if not membership and privacy not in COLLABORATIVE_PRIVACIES:
                # User is not a member and workspace is not openly shared
                return None

            # Get members
            members = WorkspaceService._get_workspace_members(workspace_id)

            # Get stats
            stats = WorkspaceService._get_workspace_stats(workspace_id)

            # Handle datetime fields - they might be datetime objects or ISO strings
            created_at = w["created_at"]
            if hasattr(created_at, 'to_native'):
                created_at = created_at.to_native()
            elif isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
            updated_at = w.get("updated_at")
            if updated_at:
                if hasattr(updated_at, 'to_native'):
                    updated_at = updated_at.to_native()
                elif isinstance(updated_at, str):
                    updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            
            # Parse view_config if present
            view_config = None
            if w.get("view_config"):
                try:
                    view_config = WorkspaceViewConfig(**w["view_config"])
                except Exception as e:
                    logger.warning(f"Failed to parse view_config for workspace {workspace_id}: {e}")
            
            return Workspace(
                workspace_id=w["workspace_id"],
                name=w["name"],
                description=w.get("description"),
                icon=w.get("icon", "📊"),
                color=w.get("color", "#3B82F6"),
                privacy=privacy,
                created_by=w["created_by"],
                created_at=created_at,
                updated_at=updated_at,
                archived=w.get("archived", False),
                members=members,
                stats=stats,
                view_config=view_config,
            )

    @staticmethod
    def list_user_workspaces(user_id: str, include_archived: bool = False) -> List[Workspace]:
        """List all workspaces for a user (includes workspaces they're members of AND public workspaces)."""
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            query = """
            MATCH (w:Workspace)
            WHERE (w.archived = $archived OR $include_archived = true)
              AND (
                coalesce(w.privacy, 'private') IN $collaborative_privacies OR
                EXISTS {
                  MATCH (:User {user_id: $user_id})-[:MEMBER_OF]->(w)
                }
              )
            OPTIONAL MATCH (u:User {user_id: $user_id})-[m:MEMBER_OF]->(w)
            RETURN DISTINCT w, m
            ORDER BY w.updated_at DESC
            """

            result = session.run(
                query,
                user_id=user_id,
                archived=False,
                include_archived=include_archived,
                collaborative_privacies=sorted(COLLABORATIVE_PRIVACIES),
            )

            workspaces = []
            for record in result:
                w = record["w"]
                members = WorkspaceService._get_workspace_members(w["workspace_id"])
                stats = WorkspaceService._get_workspace_stats(w["workspace_id"])

                # Handle datetime fields - they might be datetime objects or ISO strings
                created_at = w["created_at"]
                if hasattr(created_at, 'to_native'):
                    created_at = created_at.to_native()
                elif isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                updated_at = w.get("updated_at")
                if updated_at:
                    if hasattr(updated_at, 'to_native'):
                        updated_at = updated_at.to_native()
                    elif isinstance(updated_at, str):
                        updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))

                workspace = Workspace(
                    workspace_id=w["workspace_id"],
                    name=w["name"],
                    description=w.get("description"),
                    icon=w.get("icon", "📊"),
                    color=w.get("color", "#3B82F6"),
                    privacy=w.get("privacy", "private"),
                    created_by=w["created_by"],
                    created_at=created_at,
                    updated_at=updated_at,
                    archived=w.get("archived", False),
                    members=members,
                    stats=stats,
                )
                workspaces.append(workspace)

            return workspaces

    @staticmethod
    def get_workspace_metadata(workspace_id: str, user_id: str) -> Optional[Dict[str, object]]:
        """
        Fetch a lightweight snapshot of workspace metadata suitable for serialization.

        Used by ingestion flows to validate and, if necessary, recreate workspace nodes.
        """
        workspace = WorkspaceService.get_workspace(workspace_id, user_id)
        if not workspace:
            return None

        owner_member = next((member for member in workspace.members if member.role == "owner"), None)

        owner_permissions: List[str] = OWNER_PERMISSIONS
        if owner_member:
            perms_data = owner_member.permissions
            if isinstance(perms_data, WorkspacePermissions):
                owner_permissions = [name for name, allowed in perms_data.model_dump().items() if allowed]
            elif isinstance(perms_data, list):
                owner_permissions = perms_data
            elif isinstance(perms_data, dict):
                owner_permissions = [name for name, allowed in perms_data.items() if allowed]

        created_at_value: Optional[str]
        created_at_field = workspace.created_at
        if isinstance(created_at_field, datetime):
            created_at_value = created_at_field.isoformat()
        else:
            created_at_value = str(created_at_field) if created_at_field else None

        metadata: Dict[str, object] = {
            "workspace_id": workspace.workspace_id,
            "name": workspace.name,
            "description": workspace.description,
            "icon": workspace.icon,
            "color": workspace.color,
            "privacy": workspace.privacy,
            "created_by": workspace.created_by,
            "created_at": created_at_value,
            "owner_permissions": owner_permissions,
        }

        if owner_member:
            metadata["owner"] = {
                "user_id": owner_member.user_id,
                "email": owner_member.user_email,
                "first_name": owner_member.user_first_name,
                "last_name": owner_member.user_last_name,
            }
        else:
            metadata["owner"] = {
                "user_id": workspace.created_by,
                "email": workspace.created_by,
                "first_name": None,
                "last_name": None,
            }

        return metadata

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
        if request.view_config is not None:
            updates["view_config"] = request.view_config.dict()

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
                MATCH (w:Workspace {workspace_id: $workspace_id})
                OPTIONAL MATCH (d:Document)-[:BELONGS_TO]->(w)
                OPTIONAL MATCH (e:Entity)-[:BELONGS_TO]->(w)
                OPTIONAL MATCH (e1:Entity)-[:BELONGS_TO]->(w)
                OPTIONAL MATCH (e2:Entity)-[:BELONGS_TO]->(w)
                OPTIONAL MATCH (e1)-[rel]->(e2)
                WHERE type(rel) <> 'BELONGS_TO' AND type(rel) <> 'EXTRACTED_FROM'
                WITH w, 
                     count(DISTINCT d) as doc_count, 
                     count(DISTINCT e) as entity_count,
                     count(DISTINCT rel) as rel_count
                OPTIONAL MATCH (u:User)-[:MEMBER_OF]->(w)
                RETURN 
                    doc_count, 
                    entity_count, 
                    rel_count, 
                    count(DISTINCT u) as member_count
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
                MATCH (w:Workspace {workspace_id: $workspace_id})
                OPTIONAL MATCH (u:User {user_id: $user_id})-[m:MEMBER_OF]->(w)
                RETURN w.privacy as privacy, m.permissions as permissions, m.role as role
                """,
                user_id=user_id,
                workspace_id=workspace_id,
            )

            record = result.single()
            if not record:
                return False

            privacy = record.get("privacy") or "private"
            role = record.get("role")
            perms_data = record.get("permissions")

            if role is None:
                normalized_privacy = privacy.lower()
                # Allow read-only access to collaborative workspaces without explicit membership
                if permission == 'view' and normalized_privacy in COLLABORATIVE_PRIVACIES:
                    return True
                # Shared workspaces enable collaborative editing even without explicit membership
                if normalized_privacy == "shared" and permission in SHARED_OPEN_WRITE_PERMISSIONS:
                    return True
                return False

            # Owner has all permissions
            if role == "owner":
                return True

            if isinstance(perms_data, list):
                return permission in perms_data
            if isinstance(perms_data, dict):
                return perms_data.get(permission, False)

        return False

    @staticmethod
    def get_workspace_documents(workspace_id: str, user_id: str) -> List[dict]:
        """Get all documents in a workspace."""
        # Check if user has access to workspace
        if not WorkspaceService._user_has_permission(workspace_id, user_id, 'view'):
            logger.warning(f"User {user_id} does not have permission to view workspace {workspace_id}")
            return []

        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (d:Document)-[:BELONGS_TO]->(w:Workspace {workspace_id: $workspace_id})
                OPTIONAL MATCH (d)-[:CREATED_BY]->(u:User)
                RETURN d, u.user_email as creator_email
                ORDER BY d.created_at DESC
                """,
                workspace_id=workspace_id
            )

            documents = []
            for record in result:
                doc = record["d"]
                documents.append({
                    "document_id": doc.get("document_id"),
                    "title": doc.get("title") or doc.get("name"),
                    "name": doc.get("name"),
                    "summary": doc.get("summary"),
                    "created_at": doc.get("created_at").to_native() if doc.get("created_at") else None,
                    "updated_at": doc.get("updated_at").to_native() if doc.get("updated_at") else None,
                    "creator_email": record.get("creator_email"),
                })

            return documents

    @staticmethod
    def get_workspace_entities(workspace_id: str, user_id: str) -> List[dict]:
        """Get all entities in a workspace."""
        # Check if user has access to workspace
        if not WorkspaceService._user_has_permission(workspace_id, user_id, 'view'):
            logger.warning(f"User {user_id} does not have permission to view workspace {workspace_id}")
            return []

        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (e:Entity)-[:EXTRACTED_FROM]->(d:Document)-[:BELONGS_TO]->(w:Workspace {workspace_id: $workspace_id})
                RETURN DISTINCT e
                ORDER BY e.name
                LIMIT 500
                """,
                workspace_id=workspace_id
            )

            entities = []
            for record in result:
                entity = record["e"]
                entities.append({
                    "entity_id": entity.get("entity_id"),
                    "name": entity.get("name"),
                    "label": entity.get("label"),
                    "type": entity.get("type"),
                    "description": entity.get("description"),
                    "created_at": entity.get("created_at").to_native() if entity.get("created_at") else None,
                })

            return entities

    @staticmethod
    def get_workspace_relationships(workspace_id: str, user_id: str) -> List[dict]:
        """Get all relationships in a workspace."""
        # Check if user has access to workspace
        if not WorkspaceService._user_has_permission(workspace_id, user_id, 'view'):
            logger.warning(f"User {user_id} does not have permission to view workspace {workspace_id}")
            return []

        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            result = session.run(
                """
                MATCH (source:Entity)-[r]->(target:Entity)
                WHERE (source)-[:EXTRACTED_FROM]->(:Document)-[:BELONGS_TO]->(:Workspace {workspace_id: $workspace_id})
                AND (target)-[:EXTRACTED_FROM]->(:Document)-[:BELONGS_TO]->(:Workspace {workspace_id: $workspace_id})
                RETURN source.name as source_name, type(r) as relationship_type, target.name as target_name, r
                ORDER BY source.name
                LIMIT 500
                """,
                workspace_id=workspace_id
            )

            relationships = []
            for record in result:
                rel = record["r"]
                relationships.append({
                    "source_name": record.get("source_name"),
                    "target_name": record.get("target_name"),
                    "type": record.get("relationship_type"),
                    "relationship_type": record.get("relationship_type"),
                    "properties": dict(rel) if rel else {},
                })

            return relationships

    @staticmethod
    def add_documents_to_workspace(workspace_id: str, user_id: str, request: AddDocumentsToWorkspaceRequest) -> bool:
        """Add existing documents to a workspace (creates BELONGS_TO relationships)."""
        # Check if user has permission
        if not WorkspaceService._user_has_permission(workspace_id, user_id, 'add_documents'):
            logger.warning(f"User {user_id} does not have permission to add documents to workspace {workspace_id}")
            return False

        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            # Add BELONGS_TO relationships for documents and their entities
            result = session.run(
                """
                MATCH (w:Workspace {workspace_id: $workspace_id})
                MATCH (d:Document)
                WHERE d.document_id IN $document_ids
                MERGE (d)-[:BELONGS_TO]->(w)
                WITH d, w
                OPTIONAL MATCH (e:Entity)-[:EXTRACTED_FROM]->(d)
                FOREACH (_ IN CASE WHEN e IS NOT NULL THEN [1] ELSE [] END |
                    MERGE (e)-[:BELONGS_TO]->(w)
                )
                SET w.updated_at = datetime()
                RETURN count(DISTINCT d) as docs_added, count(DISTINCT e) as entities_linked
                """,
                workspace_id=workspace_id,
                document_ids=request.document_ids
            )

            record = result.single()
            if record:
                logger.info(f"Added {record['docs_added']} documents and {record['entities_linked']} entities to workspace {workspace_id}")
                return True

        return False

    @staticmethod
    def remove_documents_from_workspace(workspace_id: str, user_id: str, request: RemoveDocumentsFromWorkspaceRequest) -> bool:
        """Remove documents from a workspace (deletes BELONGS_TO relationships)."""
        # Check if user has permission
        if not WorkspaceService._user_has_permission(workspace_id, user_id, 'edit_relationships'):
            logger.warning(f"User {user_id} does not have permission to remove documents from workspace {workspace_id}")
            return False

        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            # Remove BELONGS_TO relationships for documents and their entities
            result = session.run(
                """
                MATCH (w:Workspace {workspace_id: $workspace_id})
                MATCH (d:Document)-[r:BELONGS_TO]->(w)
                WHERE d.document_id IN $document_ids
                DELETE r
                WITH d, w
                OPTIONAL MATCH (e:Entity)-[:EXTRACTED_FROM]->(d)
                OPTIONAL MATCH (e)-[er:BELONGS_TO]->(w)
                DELETE er
                SET w.updated_at = datetime()
                RETURN count(DISTINCT d) as docs_removed, count(DISTINCT e) as entities_unlinked
                """,
                workspace_id=workspace_id,
                document_ids=request.document_ids
            )

            record = result.single()
            if record:
                logger.info(f"Removed {record['docs_removed']} documents and {record['entities_unlinked']} entities from workspace {workspace_id}")
                return True

        return False

    @staticmethod
    def list_available_documents(user_id: str, workspace_id: Optional[str] = None) -> List[dict]:
        """List all documents available to add to a workspace (public + user's private documents)."""
        with neo4j_client._driver.session(database=settings.neo4j_database) as session:
            # If workspace_id provided, exclude documents already in that workspace
            workspace_filter = ""
            if workspace_id:
                workspace_filter = """
                AND NOT EXISTS {
                    MATCH (d)-[:BELONGS_TO]->(:Workspace {workspace_id: $workspace_id})
                }
                """

            query = f"""
            MATCH (d:Document)
            WHERE (
                NOT EXISTS {{ (d)-[:BELONGS_TO]->(:Workspace {{privacy: 'private'}}) }}
                OR EXISTS {{ (d)-[:CREATED_BY]->(:User {{user_id: $user_id}}) }}
            )
            {workspace_filter}
            OPTIONAL MATCH (d)-[:CREATED_BY]->(u:User)
            OPTIONAL MATCH (d)-[:BELONGS_TO]->(w:Workspace)
            RETURN d, u.user_email as creator_email, collect(DISTINCT w.name) as workspaces
            ORDER BY d.created_at DESC
            LIMIT 200
            """

            result = session.run(
                query,
                user_id=user_id,
                workspace_id=workspace_id
            )

            documents = []
            for record in result:
                doc = record["d"]
                documents.append({
                    "document_id": doc.get("document_id"),
                    "title": doc.get("title") or doc.get("name"),
                    "name": doc.get("name"),
                    "summary": doc.get("summary"),
                    "created_at": doc.get("created_at").to_native() if doc.get("created_at") else None,
                    "creator_email": record.get("creator_email"),
                    "workspaces": record.get("workspaces", []),
                })

            return documents


# Global service instance
workspace_service = WorkspaceService()
