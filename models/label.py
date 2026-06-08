import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin

class Label(Base, SoftDeleteMixin):
    __tablename__ = "labels"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    color = Column(String(7), nullable=True, default="#94a3b8")
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    # created_at, updated_at, deleted_at inherited from SoftDeleteMixin

    tasks = relationship("Task", secondary="task_labels", back_populates="labels")
