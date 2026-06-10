"""
Reusable SQLAlchemy mixin providing standardised audit timestamps
and soft-delete support for all entity models.

Columns added:
    created_at  – set automatically on INSERT (server-side default)
    updated_at  – set automatically on INSERT and UPDATE
    deleted_at  – NULL means active; non-NULL marks a soft-deleted row
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


class SoftDeleteMixin:
    """Mix into any SQLAlchemy model to gain audit + soft-delete columns."""

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )
    deleted_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Convenience helpers ───────────────────────────────────────

    def soft_delete(self):
        """Mark this record as deleted (sets deleted_at to now)."""
        self.deleted_at = datetime.now(timezone.utc)

    @property
    def is_deleted(self) -> bool:
        """Return True if the record has been soft-deleted."""
        return self.deleted_at is not None
