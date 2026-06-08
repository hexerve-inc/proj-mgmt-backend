"""
User-level email notification preferences.

Each row represents a user's opt-in/opt-out preference for a single
notification event type.  Rows are lazily created on first access —
if no row exists for a user+event pair the system defaults to enabled.
"""

import uuid
import enum

from sqlalchemy import Column, String, Boolean, Enum, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin


class NotificationEventType(str, enum.Enum):
    """All event types that can trigger an email notification."""

    # ── Task events ──────────────────────────────────────────────
    TASK_CREATED = "TASK_CREATED"
    TASK_STATUS_CHANGED = "TASK_STATUS_CHANGED"
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_REASSIGNED = "TASK_REASSIGNED"
    TASK_DETAILS_UPDATED = "TASK_DETAILS_UPDATED"
    TASK_DELETED = "TASK_DELETED"
    TASK_PRIORITY_CHANGED = "TASK_PRIORITY_CHANGED"
    TASK_DUE_DATE_CHANGED = "TASK_DUE_DATE_CHANGED"
    TASK_SPRINT_CHANGED = "TASK_SPRINT_CHANGED"

    # ── Comment events (future — no comment model yet) ───────────
    TASK_COMMENT_ADDED = "TASK_COMMENT_ADDED"
    TASK_COMMENT_MENTION = "TASK_COMMENT_MENTION"

    # ── Sprint events ────────────────────────────────────────────
    SPRINT_STARTED = "SPRINT_STARTED"
    SPRINT_COMPLETED = "SPRINT_COMPLETED"

    # ── Project events ───────────────────────────────────────────
    PROJECT_STATUS_CHANGED = "PROJECT_STATUS_CHANGED"


class NotificationPreference(SoftDeleteMixin, Base):
    __tablename__ = "notification_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type = Column(
        Enum(NotificationEventType, name="notification_event_type_enum"),
        nullable=False,
    )
    email_enabled = Column(Boolean, default=True, nullable=False)

    # ── Relationships ────────────────────────────────────────────
    user = relationship("User")

    # ── Constraints ──────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("user_id", "event_type", name="uq_user_event_type"),
        Index("idx_notif_pref_user", "user_id"),
    )
