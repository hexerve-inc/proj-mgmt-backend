from pydantic import BaseModel
from typing import Optional
from models.project import ProjectStatus

class ProjectBase(BaseModel):
    name: str
    status: ProjectStatus = ProjectStatus.PLANNING

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[ProjectStatus] = None

class ProjectResponse(ProjectBase):
    id: str

    class Config:
        from_attributes = True
