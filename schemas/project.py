from pydantic import BaseModel
from typing import Optional
from models.project import ProjectStatus

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    progress: int = 0
    ai_confidence: int = 85
    risk_level: str = "low"

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    progress: Optional[int] = None
    ai_confidence: Optional[int] = None
    risk_level: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: str

    class Config:
        from_attributes = True
