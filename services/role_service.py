"""
Role management service.

Handles CRUD for roles, role assignment / revocation, and audit logging.
All role mutations go through this service to ensure consistent
audit trail and privilege escalation prevention.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from models.role import Role
from models.permission import Permission
from models.role_permission import RolePermission
from models.user_role import UserRole
from models.role_audit_log import RoleAuditLog
from services.permission_service import PermissionService


class RoleService:
    """CRUD operations for roles, assignments, and audit."""

    def __init__(self, db: Session):
        self.db = db
        self._perm_service = PermissionService(db)

    # ── Role CRUD ────────────────────────────────────────────────

    def get_all_roles(self, include_inactive: bool = False) -> list[Role]:
        query = self.db.query(Role).filter(Role.deleted_at.is_(None))
        if not include_inactive:
            query = query.filter(Role.is_active.is_(True))
        return query.order_by(Role.hierarchy_level.asc()).all()

    def get_role(self, role_id: str) -> Optional[Role]:
        return (
            self.db.query(Role)
            .filter(Role.id == role_id, Role.deleted_at.is_(None))
            .first()
        )

    def get_role_by_slug(self, slug: str) -> Optional[Role]:
        return (
            self.db.query(Role)
            .filter(Role.slug == slug, Role.deleted_at.is_(None))
            .first()
        )

    def create_role(
        self,
        name: str,
        slug: str,
        description: Optional[str],
        hierarchy_level: int,
        permission_ids: list[str],
        actor_id: str,
    ) -> Role:
        """Create a custom role with the given permissions."""
        # Validate slug uniqueness
        if self.get_role_by_slug(slug):
            raise HTTPException(status_code=400, detail=f"Role slug '{slug}' already exists")

        role = Role(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            description=description,
            is_system=False,
            is_active=True,
            hierarchy_level=hierarchy_level,
        )
        self.db.add(role)
        self.db.flush()

        # Add permission mappings
        for perm_id in permission_ids:
            rp = RolePermission(
                id=str(uuid.uuid4()),
                role_id=role.id,
                permission_id=perm_id,
            )
            self.db.add(rp)

        # Audit log
        self._audit(
            user_id=actor_id,
            actor_id=actor_id,
            action="role_created",
            role_id=role.id,
            new_value={"name": name, "slug": slug, "permissions": permission_ids},
        )

        self.db.commit()
        self.db.refresh(role)
        return role

    def update_role(
        self,
        role_id: str,
        updates: dict,
        actor_id: str,
    ) -> Optional[Role]:
        """Update a custom role. System roles cannot be modified."""
        role = self.get_role(role_id)
        if not role:
            return None
        if role.is_system:
            raise HTTPException(status_code=400, detail="System roles cannot be modified")

        old_value = {"name": role.name, "description": role.description}

        if "name" in updates:
            role.name = updates["name"]
        if "description" in updates:
            role.description = updates["description"]
        if "hierarchy_level" in updates:
            role.hierarchy_level = updates["hierarchy_level"]
        if "is_active" in updates:
            role.is_active = updates["is_active"]

        # Update permissions if provided
        if "permission_ids" in updates:
            # Remove existing
            self.db.query(RolePermission).filter(
                RolePermission.role_id == role_id
            ).delete()
            # Add new
            for perm_id in updates["permission_ids"]:
                rp = RolePermission(
                    id=str(uuid.uuid4()),
                    role_id=role_id,
                    permission_id=perm_id,
                )
                self.db.add(rp)

        self._audit(
            user_id=actor_id,
            actor_id=actor_id,
            action="role_updated",
            role_id=role_id,
            old_value=old_value,
            new_value=updates,
        )

        self.db.commit()
        self.db.refresh(role)
        return role

    def delete_role(self, role_id: str, actor_id: str) -> bool:
        """Soft-delete a custom role. System roles cannot be deleted."""
        role = self.get_role(role_id)
        if not role:
            return False
        if role.is_system:
            raise HTTPException(status_code=400, detail="System roles cannot be deleted")

        # Check if any users still have this role
        active_assignments = (
            self.db.query(UserRole)
            .filter(
                UserRole.role_id == role_id,
                UserRole.revoked_at.is_(None),
                UserRole.deleted_at.is_(None),
            )
            .count()
        )
        if active_assignments > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete role: {active_assignments} user(s) still assigned",
            )

        role.soft_delete()
        self._audit(
            user_id=actor_id,
            actor_id=actor_id,
            action="role_deleted",
            role_id=role_id,
            old_value={"name": role.name, "slug": role.slug},
        )
        self.db.commit()
        return True

    # ── Role Assignment ──────────────────────────────────────────

    def assign_role(
        self,
        user_id: str,
        role_id: str,
        scope_type: str = "global",
        scope_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> UserRole:
        """Assign a role to a user with optional scope and expiry."""
        role = self.get_role(role_id)
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        # Privilege escalation check
        if actor_id:
            actor_level = self._perm_service.get_user_highest_hierarchy_level(actor_id)
            if role.hierarchy_level <= actor_level and actor_id != user_id:
                raise HTTPException(
                    status_code=403,
                    detail="Cannot assign a role with equal or higher privilege than your own",
                )

        # Check for existing active assignment
        existing = (
            self.db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.role_id == role_id,
                UserRole.scope_type == scope_type,
                UserRole.revoked_at.is_(None),
                UserRole.deleted_at.is_(None),
            )
        )
        if scope_id:
            existing = existing.filter(UserRole.scope_id == scope_id)
        else:
            existing = existing.filter(UserRole.scope_id.is_(None))

        if existing.first():
            raise HTTPException(status_code=400, detail="User already has this role in this scope")

        assignment = UserRole(
            id=str(uuid.uuid4()),
            user_id=user_id,
            role_id=role_id,
            scope_type=scope_type,
            scope_id=scope_id,
            assigned_by=actor_id,
            expires_at=expires_at,
        )
        self.db.add(assignment)

        self._audit(
            user_id=user_id,
            actor_id=actor_id or "system",
            action="role_assigned",
            role_id=role_id,
            scope_type=scope_type,
            scope_id=scope_id,
            new_value={
                "role_slug": role.slug,
                "scope_type": scope_type,
                "scope_id": scope_id,
                "expires_at": expires_at.isoformat() if expires_at else None,
            },
        )

        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def revoke_role(
        self,
        user_id: str,
        role_id: str,
        scope_type: str = "global",
        scope_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> bool:
        """Soft-revoke a role assignment."""
        query = self.db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.scope_type == scope_type,
            UserRole.revoked_at.is_(None),
            UserRole.deleted_at.is_(None),
        )
        if scope_id:
            query = query.filter(UserRole.scope_id == scope_id)
        else:
            query = query.filter(UserRole.scope_id.is_(None))

        assignment = query.first()
        if not assignment:
            return False

        assignment.revoked_at = datetime.now(timezone.utc)

        role = self.get_role(role_id)
        self._audit(
            user_id=user_id,
            actor_id=actor_id or "system",
            action="role_revoked",
            role_id=role_id,
            scope_type=scope_type,
            scope_id=scope_id,
            old_value={
                "role_slug": role.slug if role else role_id,
                "scope_type": scope_type,
                "scope_id": scope_id,
            },
        )

        self.db.commit()
        return True

    # ── Role Permissions ─────────────────────────────────────────

    def get_role_permissions(self, role_id: str) -> list[Permission]:
        """Return all permissions granted to a role."""
        return (
            self.db.query(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .filter(RolePermission.role_id == role_id)
            .order_by(Permission.module, Permission.action)
            .all()
        )

    def get_all_permissions(self) -> list[Permission]:
        """Return all permissions in the system."""
        return self.db.query(Permission).order_by(Permission.module, Permission.action).all()

    # ── Audit ────────────────────────────────────────────────────

    def _audit(
        self,
        user_id: str,
        actor_id: str,
        action: str,
        role_id: Optional[str] = None,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
    ) -> None:
        log = RoleAuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            actor_id=actor_id,
            action=action,
            role_id=role_id,
            scope_type=scope_type,
            scope_id=scope_id,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.add(log)

    def get_audit_log(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RoleAuditLog]:
        """Retrieve audit log entries, optionally filtered by user."""
        query = self.db.query(RoleAuditLog)
        if user_id:
            query = query.filter(RoleAuditLog.user_id == user_id)
        return (
            query.order_by(RoleAuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
