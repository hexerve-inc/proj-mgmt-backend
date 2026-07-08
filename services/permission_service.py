"""
Centralized permission resolution engine.

This is the **single source of truth** for all authorization decisions.
Every permission check in the application flows through this service.

Resolution strategy:
1. Load all active (non-revoked, non-expired, non-deleted) user_roles for the user.
2. For each role, load its granted permission codes.
3. Union all permission codes across all roles.
4. If checking a scoped permission, include both global roles AND
   roles scoped to the specific entity.

Performance: per-request caching ensures that repeated permission
checks within the same request do not hit the database again.
"""

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from models.user_role import UserRole
from models.role import Role
from models.role_permission import RolePermission
from models.permission import Permission


class PermissionService:
    """Centralized permission resolution engine."""

    def __init__(self, db: Session):
        self.db = db
        self._cache: dict[str, set[str]] = {}

    def _cache_key(self, user_id: str, scope_type: Optional[str], scope_id: Optional[str]) -> str:
        return f"{user_id}:{scope_type or 'any'}:{scope_id or 'any'}"

    def get_user_permissions(
        self,
        user_id: str,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
    ) -> set[str]:
        """Resolve all permission codes for a user.

        Returns the union of permissions from:
        - All global roles the user holds
        - If scope_type/scope_id provided, also roles scoped to that entity
        """
        key = self._cache_key(user_id, scope_type, scope_id)
        if key in self._cache:
            return self._cache[key]

        now = datetime.now(timezone.utc)

        # Build query for active user_roles
        query = (
            self.db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.revoked_at.is_(None),
                UserRole.deleted_at.is_(None),
            )
            .filter(
                (UserRole.expires_at.is_(None)) | (UserRole.expires_at > now)
            )
        )

        # Include global roles + scoped roles if scope specified
        if scope_type and scope_id:
            query = query.filter(
                (UserRole.scope_type == "global")
                | (
                    (UserRole.scope_type == scope_type)
                    & (UserRole.scope_id == scope_id)
                )
            )
        # If no scope specified, load ALL roles (global + any scoped)
        # This gives the broadest permission set

        user_role_records = query.all()
        role_ids = [ur.role_id for ur in user_role_records]

        if not role_ids:
            self._cache[key] = set()
            return set()

        # Load permission codes for these roles
        perm_codes = (
            self.db.query(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(RolePermission.role_id.in_(role_ids))
            .distinct()
            .all()
        )

        result = {row[0] for row in perm_codes}
        self._cache[key] = result
        return result

    def has_permission(
        self,
        user_id: str,
        permission: str,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
    ) -> bool:
        """Check if a user has a specific permission."""
        permissions = self.get_user_permissions(user_id, scope_type, scope_id)
        # Wildcard check
        if "*" in permissions:
            return True
        return permission in permissions

    def check_permission(
        self,
        user_id: str,
        permission: str,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
    ) -> None:
        """Raise HTTP 403 if the user lacks the specified permission."""
        if not self.has_permission(user_id, permission, scope_type, scope_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}",
            )

    def get_user_roles(self, user_id: str) -> list[dict]:
        """Return all active role assignments for a user."""
        now = datetime.now(timezone.utc)

        records = (
            self.db.query(UserRole)
            .options(joinedload(UserRole.role))
            .filter(
                UserRole.user_id == user_id,
                UserRole.revoked_at.is_(None),
                UserRole.deleted_at.is_(None),
            )
            .filter(
                (UserRole.expires_at.is_(None)) | (UserRole.expires_at > now)
            )
            .all()
        )

        return [
            {
                "id": ur.id,
                "role_id": ur.role_id,
                "role_name": ur.role.name if ur.role else None,
                "role_slug": ur.role.slug if ur.role else None,
                "scope_type": ur.scope_type,
                "scope_id": ur.scope_id,
                "assigned_at": ur.assigned_at.isoformat() if ur.assigned_at else None,
                "expires_at": ur.expires_at.isoformat() if ur.expires_at else None,
            }
            for ur in records
        ]

    def get_accessible_project_ids(self, user_id: str) -> Optional[list[str]]:
        """Return project IDs the user can access, or None for unrestricted (admins).

        - Users with global admin-level roles → None (all projects)
        - Users with project-scoped roles → list of those project IDs
        - Users with team-based roles → project IDs via team membership (future)
        """
        permissions = self.get_user_permissions(user_id)

        # Admins can access everything
        if "*" in permissions:
            return None

        now = datetime.now(timezone.utc)

        # Check for global roles that grant broad read access
        global_roles = (
            self.db.query(UserRole)
            .options(joinedload(UserRole.role))
            .filter(
                UserRole.user_id == user_id,
                UserRole.scope_type == "global",
                UserRole.revoked_at.is_(None),
                UserRole.deleted_at.is_(None),
            )
            .filter(
                (UserRole.expires_at.is_(None)) | (UserRole.expires_at > now)
            )
            .all()
        )

        # If user has any global role with hierarchy_level <= 50, they see all projects
        for ur in global_roles:
            if ur.role and ur.role.hierarchy_level <= 50:
                return None

        # Otherwise, return only project-scoped project IDs
        scoped_records = (
            self.db.query(UserRole.scope_id)
            .filter(
                UserRole.user_id == user_id,
                UserRole.scope_type == "project",
                UserRole.scope_id.isnot(None),
                UserRole.revoked_at.is_(None),
                UserRole.deleted_at.is_(None),
            )
            .filter(
                (UserRole.expires_at.is_(None)) | (UserRole.expires_at > now)
            )
            .distinct()
            .all()
        )

        return [r[0] for r in scoped_records]

    def get_user_highest_hierarchy_level(self, user_id: str) -> int:
        """Return the lowest (most privileged) hierarchy_level across all user roles.

        Used for privilege escalation prevention: a user can only assign
        roles with a *higher* hierarchy_level than their own.
        Returns 999 if the user has no roles.
        """
        now = datetime.now(timezone.utc)

        result = (
            self.db.query(Role.hierarchy_level)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(
                UserRole.user_id == user_id,
                UserRole.revoked_at.is_(None),
                UserRole.deleted_at.is_(None),
            )
            .filter(
                (UserRole.expires_at.is_(None)) | (UserRole.expires_at > now)
            )
            .order_by(Role.hierarchy_level.asc())
            .first()
        )

        return result[0] if result else 999
