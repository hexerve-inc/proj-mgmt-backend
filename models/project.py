import uuid
from sqlalchemy import Column, String, Enum, ForeignKey
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
    team_id = Column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=True) # Or nullable=False depending on logic
    client_id = Column(String, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    program_id = Column(String, ForeignKey("programs.id", ondelete="SET NULL"), nullable=True)
    
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    team = relationship("Team", back_populates="projects")
    client = relationship("Client", back_populates="projects")
    program = relationship("Program", back_populates="projects")
    invoices = relationship("Invoice", back_populates="project")
