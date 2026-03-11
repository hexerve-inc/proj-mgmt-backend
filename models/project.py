import uuid
from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
from core.database import Base
import enum

class ProjectStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    status = Column(Enum(ProjectStatus, name="project_status_enum"), default=ProjectStatus.PLANNING, nullable=False)
    
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
