import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin

class TaskGroup(SoftDeleteMixin, Base):
    __tablename__ = "task_groups"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(150), nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)

    tasks = relationship("Task", backref="group")
