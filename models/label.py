import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class Label(Base):
    __tablename__ = "labels"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    color = Column(String(7), nullable=True, default="#94a3b8")
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    tasks = relationship("Task", secondary="task_labels", back_populates="labels")
