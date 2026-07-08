"""
Pydantic schemas for the RBAC system.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Permission schemas ───────────────────────────────────────────

class PermissionResponse(BaseModel):
    id: str
    code: str
    module: str
    action: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ── Role schemas ─────────────────────────────────────────────────

class RoleBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100)
    description: Optional[str] = None
    hierarchy_level: int = Field(default=100, ge=0)


class RoleCreate(RoleBase):
    permission_ids: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    hierarchy_level: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    permission_ids: Optional[list[str]] = None


class RoleResponse(RoleBase):
    id: str
    is_system: bool
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoleDetailResponse(RoleResponse):
    """Role with its granted permissions."""
    permissions: list[PermissionResponse] = []


# ── User-Role assignment schemas ─────────────────────────────────

class RoleAssignmentCreate(BaseModel):
    role_id: str
    scope_type: str = Field(default="global", pattern="^(global|project|team)$")
    scope_id: Optional[str] = None
    expires_at: Optional[datetime] = None


class RoleAssignmentResponse(BaseModel):
    id: str
    role_id: str
    role_name: Optional[str] = None
    role_slug: Optional[str] = None
    scope_type: str
    scope_id: Optional[str] = None
    assigned_at: Optional[str] = None
    expires_at: Optional[str] = None


class RoleRevoke(BaseModel):
    scope_type: str = Field(default="global", pattern="^(global|project|team)$")
    scope_id: Optional[str] = None


# ── User permissions response ────────────────────────────────────

class UserPermissionsResponse(BaseModel):
    """Returned by GET /users/me/permissions."""
    user_id: str
    permissions: list[str]
    roles: list[RoleAssignmentResponse]


# ── Audit log schemas ────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: str
    user_id: str
    actor_id: str
    action: str
    role_id: Optional[str] = None
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True
