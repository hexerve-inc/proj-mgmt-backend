"""
Permission model for the RBAC system.

Each permission represents a single granular action within a module.
Permissions are seeded at deployment time and should not be created
via the API (only role-permission *mappings* change).

Naming convention: ``<module>:<action>``
Examples: ``tasks:create``, ``projects:delete``, ``analytics:export``
"""

import uuid

from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(100), nullable=False, unique=True, index=True)
    module = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ────────────────────────────────────────────
    role_permissions = relationship(
        "RolePermission", back_populates="permission", cascade="all, delete-orphan"
    )

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_perm_module", "module"),
    )

    def __repr__(self) -> str:
        return f"<Permission {self.code}>"
