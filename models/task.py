import uuid
from sqlalchemy import Column, String, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from core.database import Base
import enum

class TaskStatus(str, enum.Enum):
    TODO = "TODO"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"

class Priority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_code = Column(String, unique=True, nullable=False, index=True) # Unique code, e.g. PROJ-123
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(TaskStatus, name="task_status_enum"), default=TaskStatus.TODO, nullable=False)
    priority = Column(Enum(Priority, name="priority_enum"), default=Priority.MEDIUM, nullable=False)
    progress = Column(Integer, default=0)
    story_points = Column(Integer, nullable=True, default=0)
    
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    project = relationship("Project", back_populates="tasks")
    
    sprint_id = Column(String, ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True)
    sprint = relationship("Sprint", back_populates="tasks")
    
    assignee_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assignee = relationship("User")
