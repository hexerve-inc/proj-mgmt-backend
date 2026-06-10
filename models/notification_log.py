"""
Notification delivery log for auditing, debugging, and deduplication.

Every notification attempt (sent, failed, or skipped) is recorded here
so administrators can trace delivery issues and the system can enforce
deduplication windows via the idempotency_key column.
"""

import uuid

from sqlalchemy import Column, String, ForeignKey, Text, Index, DateTime
from sqlalchemy.sql import func
from core.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type = Column(String(30), nullable=False)       # e.g. "TASK_CREATED"
    entity_id = Column(String(36), nullable=False)        # Task / Sprint / Project UUID
    entity_type = Column(String(20), nullable=False)      # "task", "sprint", "project"

    email_to = Column(String(320), nullable=False)        # RFC 5321 max email length
    email_subject = Column(String(500), nullable=False)   # generous limit for subjects
    status = Column(String(10), nullable=False)           # "sent", "failed", "skipped"
    error_message = Column(Text, nullable=True)

    # Deduplication: hash of (user_id, event_type, entity_id, 5-min bucket)
    # SHA-256 hex digest = exactly 64 chars; unique=True creates a B-tree index automatically
    idempotency_key = Column(String(64), unique=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_notif_log_user_created", "user_id", "created_at"),
        # NOTE: No separate index on idempotency_key — the unique constraint
        # already provides a B-tree index for lookups.
    )
