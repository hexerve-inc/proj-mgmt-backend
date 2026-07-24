import uuid
from sqlalchemy import Column, String, Enum, ForeignKey, Integer, Date
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin
import enum

class ProjectStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"

class Project(SoftDeleteMixin, Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False, index=True)
    project_key = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    status = Column(Enum(ProjectStatus, name="project_status_enum"), default=ProjectStatus.PLANNING, nullable=False)
    team_id = Column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=True)
    client_id = Column(String, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    program_id = Column(String, ForeignKey("programs.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    template_id = Column(String(50), nullable=True, index=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    progress = Column(Integer, default=0)
    ai_confidence = Column(Integer, default=85)
    risk_level = Column(String, default="low") # low, medium, high, critical
    task_count = Column(Integer, default=0, nullable=False)
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    workflow_statuses = relationship("WorkflowStatus", back_populates="project", cascade="all, delete-orphan")
    team = relationship("Team", back_populates="projects")
    client = relationship("Client", back_populates="projects")
    program = relationship("Program", back_populates="projects")
    invoices = relationship("Invoice", back_populates="project")
    custom_filters = relationship("CustomFilter", back_populates="project", cascade="all, delete-orphan")
