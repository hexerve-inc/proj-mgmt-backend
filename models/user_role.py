"""
User-Role assignment model.

Supports three scope types:
- ``global``  — the role applies system-wide (scope_id is NULL)
- ``project`` — the role applies only within a specific project
- ``team``    — the role applies only within a specific team

Features:
- **Expiry**: set ``expires_at`` for temporary access (e.g. contractor).
- **Soft revocation**: set ``revoked_at`` to disable without deleting.
- **Audit**: ``assigned_by`` tracks who granted the role.
"""

import uuid

from sqlalchemy import Column, String, ForeignKey, DateTime, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin


class UserRole(SoftDeleteMixin, Base):
    __tablename__ = "user_roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_id = Column(
        String,
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope_type = Column(String(20), nullable=False, default="global")  # global | project | team
    scope_id = Column(String, nullable=True)  # project_id or team_id; NULL for global
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(String, ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    # created_at, updated_at, deleted_at inherited from SoftDeleteMixin

    # ── Relationships ────────────────────────────────────────────
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    assigner = relationship("User", foreign_keys=[assigned_by])

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_user_role_scope", "user_id", "role_id", "scope_type", "scope_id"),
        Index("idx_user_role_user", "user_id"),
    )

    @property
    def is_active(self) -> bool:
        """True if the assignment is not revoked, not expired, and not deleted."""
        from datetime import datetime, timezone

        if self.revoked_at is not None:
            return False
        if self.deleted_at is not None:
            return False
        if self.expires_at is not None and self.expires_at < datetime.now(timezone.utc):
            return False
        return True

    def __repr__(self) -> str:
        return (
            f"<UserRole user={self.user_id} role={self.role_id} "
            f"scope={self.scope_type}:{self.scope_id}>"
        )
