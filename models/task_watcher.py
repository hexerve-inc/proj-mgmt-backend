"""
Task Watcher model — tracks which users are watching (subscribed to) a task.

Each row represents an active or soft-deleted subscription.  When a user
"unwatches" a task the row is soft-deleted rather than removed, allowing
the system to re-activate the same row if the user re-watches.
"""

import uuid

from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin


class TaskWatcher(SoftDeleteMixin, Base):
    __tablename__ = "task_watchers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(
        String,
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    task = relationship("Task", back_populates="watcher_records")
    user = relationship("User")

    # ── Constraints & Indexes ────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("task_id", "user_id", name="uq_task_watcher"),
        Index("idx_task_watcher_task", "task_id"),
        Index("idx_task_watcher_user", "user_id"),
    )
