"""
Role management API routes.

Provides endpoints for:
- Listing all roles and permissions
- Creating / updating / deleting custom roles
- Assigning / revoking roles for users
- Fetching the current user's resolved permissions
- Viewing the role audit log
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user, require_permission, get_permission_service
from models.user import User
from services.role_service import RoleService
from services.permission_service import PermissionService
from schemas.role import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleDetailResponse,
    PermissionResponse,
    RoleAssignmentCreate,
    RoleAssignmentResponse,
    RoleRevoke,
    UserPermissionsResponse,
    AuditLogResponse,
)

router = APIRouter(prefix="/roles", tags=["roles"])


# ── Role listing & details ───────────────────────────────────────

@router.get("/", response_model=list[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active roles. Available to any authenticated user."""
    svc = RoleService(db)
    roles = svc.get_all_roles()
    return roles


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all permissions in the system. For role management UIs."""
    svc = RoleService(db)
    return svc.get_all_permissions()


@router.get("/{role_id}", response_model=RoleDetailResponse)
def get_role_detail(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a role with its granted permissions."""
    svc = RoleService(db)
    role = svc.get_role(role_id)
    if not role:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Role not found")
    permissions = svc.get_role_permissions(role_id)
    return RoleDetailResponse(
        id=role.id,
        name=role.name,
        slug=role.slug,
        description=role.description,
        hierarchy_level=role.hierarchy_level,
        is_system=role.is_system,
        is_active=role.is_active,
        created_at=role.created_at,
        permissions=[PermissionResponse.model_validate(p) for p in permissions],
    )


# ── Role CRUD (requires roles:manage / roles:create_custom) ──────

@router.post("/", response_model=RoleResponse)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service: PermissionService = Depends(get_permission_service),
):
    """Create a custom role. Requires roles:create_custom permission."""
    perm_service.check_permission(current_user.id, "roles:create_custom")
    svc = RoleService(db)
    role = svc.create_role(
        name=role_in.name,
        slug=role_in.slug,
        description=role_in.description,
        hierarchy_level=role_in.hierarchy_level,
        permission_ids=role_in.permission_ids,
        actor_id=current_user.id,
    )
    return role


@router.patch("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: str,
    role_in: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service: PermissionService = Depends(get_permission_service),
):
    """Update a custom role. System roles cannot be modified."""
    perm_service.check_permission(current_user.id, "roles:manage")
    svc = RoleService(db)
    updates = role_in.model_dump(exclude_unset=True)
    role = svc.update_role(role_id, updates, actor_id=current_user.id)
    if not role:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.delete("/{role_id}")
def delete_role(
    role_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service: PermissionService = Depends(get_permission_service),
):
    """Delete a custom role (soft-delete). Cannot delete if users are assigned."""
    perm_service.check_permission(current_user.id, "roles:manage")
    svc = RoleService(db)
    deleted = svc.delete_role(role_id, actor_id=current_user.id)
    if not deleted:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Role not found")
    return {"detail": "Role deleted"}


# ── User role assignment ─────────────────────────────────────────

@router.post("/users/{user_id}/roles", response_model=RoleAssignmentResponse)
def assign_user_role(
    user_id: str,
    assignment_in: RoleAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service: PermissionService = Depends(get_permission_service),
):
    """Assign a role to a user. Requires roles:assign permission."""
    perm_service.check_permission(current_user.id, "roles:assign")
    svc = RoleService(db)
    assignment = svc.assign_role(
        user_id=user_id,
        role_id=assignment_in.role_id,
        scope_type=assignment_in.scope_type,
        scope_id=assignment_in.scope_id,
        actor_id=current_user.id,
        expires_at=assignment_in.expires_at,
    )
    role = svc.get_role(assignment.role_id)
    return RoleAssignmentResponse(
        id=assignment.id,
        role_id=assignment.role_id,
        role_name=role.name if role else None,
        role_slug=role.slug if role else None,
        scope_type=assignment.scope_type,
        scope_id=assignment.scope_id,
        assigned_at=assignment.assigned_at.isoformat() if assignment.assigned_at else None,
        expires_at=assignment.expires_at.isoformat() if assignment.expires_at else None,
    )


@router.delete("/users/{user_id}/roles/{role_id}")
def revoke_user_role(
    user_id: str,
    role_id: str,
    revoke_in: RoleRevoke = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service: PermissionService = Depends(get_permission_service),
):
    """Revoke a role from a user."""
    perm_service.check_permission(current_user.id, "roles:assign")
    svc = RoleService(db)
    scope_type = revoke_in.scope_type if revoke_in else "global"
    scope_id = revoke_in.scope_id if revoke_in else None
    revoked = svc.revoke_role(
        user_id=user_id,
        role_id=role_id,
        scope_type=scope_type,
        scope_id=scope_id,
        actor_id=current_user.id,
    )
    if not revoked:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Active role assignment not found")
    return {"detail": "Role revoked"}


@router.get("/users/{user_id}/roles", response_model=list[RoleAssignmentResponse])
def list_user_roles(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service: PermissionService = Depends(get_permission_service),
):
    """List all active roles for a user. Requires roles:read permission."""
    perm_service.check_permission(current_user.id, "roles:read")
    perm_svc = PermissionService(db)
    return perm_svc.get_user_roles(user_id)


# ── Current user permissions ─────────────────────────────────────

@router.get("/me/permissions", response_model=UserPermissionsResponse)
def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's resolved permissions and roles."""
    perm_svc = PermissionService(db)
    permissions = list(perm_svc.get_user_permissions(current_user.id))
    roles = perm_svc.get_user_roles(current_user.id)
    return UserPermissionsResponse(
        user_id=current_user.id,
        permissions=sorted(permissions),
        roles=[RoleAssignmentResponse(**r) for r in roles],
    )


# ── Audit log ────────────────────────────────────────────────────

@router.get("/audit-log", response_model=list[AuditLogResponse])
def get_audit_log(
    user_id: str = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service: PermissionService = Depends(get_permission_service),
):
    """View role audit log. Requires roles:manage permission."""
    perm_service.check_permission(current_user.id, "roles:manage")
    svc = RoleService(db)
    return svc.get_audit_log(user_id=user_id, limit=limit, offset=offset)
