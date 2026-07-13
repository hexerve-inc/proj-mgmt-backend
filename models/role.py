"""
Role model for the RBAC system.

Each role is a named collection of permissions. Roles can be:
- System roles (is_system=True): Predefined, cannot be deleted or renamed.
- Custom roles (is_system=False): Created by org admins, fully editable.

The `hierarchy_level` field controls privilege escalation prevention:
a user can only assign roles with a *higher* (less privileged) level
than their own highest role.
"""

import uuid

from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.orm import relationship

from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin


class Role(SoftDeleteMixin, Base):
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    hierarchy_level = Column(Integer, nullable=False, default=0)
    # created_at, updated_at, deleted_at inherited from SoftDeleteMixin

    # ── Relationships ────────────────────────────────────────────
    role_permissions = relationship(
        "RolePermission", back_populates="role", cascade="all, delete-orphan"
    )
    user_roles = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Role {self.slug} (level={self.hierarchy_level})>"
