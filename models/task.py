import uuid
import enum
from sqlalchemy import Column, String, Enum, ForeignKey, Integer, Date, Table
from sqlalchemy.orm import relationship
from core.database import Base

# Association table for many-to-many Task <-> Label
task_labels = Table(
    'task_labels',
    Base.metadata,
    Column('task_id', String, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('label_id', String, ForeignKey('labels.id', ondelete='CASCADE'), primary_key=True),
)


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
    status_id = Column(String, ForeignKey("workflow_statuses.id"), nullable=False)
    priority = Column(Enum(Priority, name="priority_enum"), default=Priority.MEDIUM, nullable=False)
    progress = Column(Integer, default=0)
    story_points = Column(Integer, nullable=True, default=0)
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    
    
    # New grouping and labels
    group_id = Column(String, ForeignKey("task_groups.id", ondelete="SET NULL"), nullable=True)
    labels = relationship("Label", secondary=task_labels, back_populates="tasks")
    
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    project = relationship("Project", back_populates="tasks")
    status = relationship("WorkflowStatus")
    
    sprint_id = Column(String, ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True)
    sprint = relationship("Sprint", back_populates="tasks")
    
    assignee_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assignee = relationship("User")
