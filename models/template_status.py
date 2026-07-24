import uuid

from sqlalchemy import (
    Column,
    String,
    Enum,
    Integer,
    Boolean,
)
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin
from models.workflow_status import WorkflowGroup


class TemplateStatus(SoftDeleteMixin, Base):
    """System-level default statuses for a specific project template.
    
    When a project is created using a template, these statuses are copied
    into the project's own workflow_statuses table.
    """
    __tablename__ = "template_statuses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(50), nullable=False, index=True)  # e.g. "tpl-lead", "tpl-blank"
    name = Column(String(100), nullable=False)
    group_key = Column(
        Enum(WorkflowGroup, name="workflow_group_enum"),
        nullable=False,
    )
    color = Column(String(7), default="#6B7280")
    position = Column(Integer, default=0, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    # created_at, updated_at, deleted_at inherited from SoftDeleteMixin
