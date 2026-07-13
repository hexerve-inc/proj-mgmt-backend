"""
Database-driven outgoing email (SMTP) configuration.

Stores the active SMTP settings so administrators can change the
outgoing email identity from the Settings UI without a code
deployment or application restart.

Only one row should have ``is_active=True`` at any time — the
service layer enforces this invariant.  Previous configurations
are soft-deleted and retained for audit history.
"""

import uuid

from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Text,
    ForeignKey,
    DateTime,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin


class EmailConfiguration(SoftDeleteMixin, Base):
    __tablename__ = "email_configurations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # ── Sender identity ──────────────────────────────────────────
    sender_email = Column(String(320), nullable=False)       # RFC 5321 max
    sender_name = Column(String(200), nullable=False)

    # ── SMTP connection ──────────────────────────────────────────
    smtp_host = Column(String(255), nullable=False)
    smtp_port = Column(Integer, nullable=False, default=587)
    smtp_username = Column(String(320), nullable=True)
    smtp_password_encrypted = Column(Text, nullable=True)    # Fernet-encrypted

    # TLS | SSL | NONE
    encryption_type = Column(String(10), nullable=False, default="TLS")

    # ── Operational flags ────────────────────────────────────────
    is_enabled = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)

    # ── Test / status tracking ───────────────────────────────────
    last_tested_at = Column(DateTime(timezone=True), nullable=True)
    last_test_status = Column(String(20), nullable=True)     # "success" | "failed"
    last_test_error = Column(String(500), nullable=True)

    # ── Audit ────────────────────────────────────────────────────
    configured_by_id = Column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────
    configured_by = relationship("User", foreign_keys=[configured_by_id])

    # ── Indexes ──────────────────────────────────────────────────
    __table_args__ = (
        Index("idx_email_config_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<EmailConfiguration {self.sender_email} active={self.is_active}>"
