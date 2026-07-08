"""
Immutable audit log for role-related changes.

Every role assignment, revocation, creation, or modification is logged.
This table is append-only — rows should never be updated or deleted.

Actions tracked:
- ``role_assigned``    — a role was given to a user
- ``role_revoked``     — a role was taken from a user
- ``role_expired``     — a role assignment expired automatically
- ``role_created``     — a new custom role was created
- ``role_updated``     — a role definition was changed
- ``role_deleted``     — a role was soft-deleted
"""

import uuid

from sqlalchemy import Column, String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from core.database import Base


class RoleAuditLog(Base):
    __tablename__ = "role_audit_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)       # The user whose role changed
    actor_id = Column(String, nullable=False, index=True)      # Who made the change
    action = Column(String(50), nullable=False)                # role_assigned, role_revoked, etc.
    role_id = Column(String, nullable=True)                    # The role involved
    scope_type = Column(String(20), nullable=True)             # global | project | team
    scope_id = Column(String, nullable=True)                   # project_id or team_id
    old_value = Column(JSONB, nullable=True)                   # Previous state
    new_value = Column(JSONB, nullable=True)                   # New state
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_audit_user_action", "user_id", "action"),
        Index("idx_audit_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<RoleAuditLog {self.action} user={self.user_id} by={self.actor_id}>"
