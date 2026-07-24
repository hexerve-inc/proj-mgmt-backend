import uuid
import enum

from sqlalchemy import (
    Column,
    String,
    Enum,
    ForeignKey,
    Integer,
    Boolean,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin


class WorkflowGroup(str, enum.Enum):
    """Immutable system-level workflow groups.

    These four groups are the anchors used across all analytics,
    sprint velocity calculations, progress tracking, and automation.
    Custom statuses are always nested under one of these groups.
    """
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    CLOSED = "CLOSED"


class WorkflowStatus(SoftDeleteMixin, Base):
    """Per-project custom status within a workflow group.

    Each project has its own set of statuses (e.g. "To Do", "In Review").
    Every status belongs to exactly one WorkflowGroup, which determines
    how the system interprets it for sprint completion, progress, and reports.
    """
    __tablename__ = "workflow_statuses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(
        String,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    group_key = Column(
        Enum(WorkflowGroup, name="workflow_group_enum"),
        nullable=False,
    )
    color = Column(String(7), default="#6B7280")
    icon = Column(String(50), nullable=True)
    position = Column(Integer, default=0, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    template_status_id = Column(
        String,
        ForeignKey("template_statuses.id", ondelete="SET NULL"),
        nullable=True,
    )
    # created_at, updated_at, deleted_at inherited from SoftDeleteMixin

    # ── Constraints ──────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("project_id", "slug", name="uq_project_status_slug"),
        Index("idx_ws_project", "project_id"),
        Index("idx_ws_group", "group_key"),
    )

    # ── Relationships ────────────────────────────────────────────
    project = relationship("Project", back_populates="workflow_statuses")
