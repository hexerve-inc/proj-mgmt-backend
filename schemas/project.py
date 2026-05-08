from datetime import date
from pydantic import AliasChoices, BaseModel, Field
from typing import Optional
from models.project import ProjectStatus

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    progress: Optional[int] = 0
    ai_confidence: Optional[int] = 85
    risk_level: Optional[str] = "low"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    client_id: Optional[str] = None
    team_id: Optional[str] = None
    program_id: Optional[str] = None

class ProjectCreate(ProjectBase):
    project_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("project_key", "key"),
    )

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    project_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("project_key", "key"),
    )
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    progress: Optional[int] = None
    ai_confidence: Optional[int] = None
    risk_level: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    client_id: Optional[str] = None
    team_id: Optional[str] = None
    program_id: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: str
    project_key: str
    task_count: int

    class Config:
        from_attributes = True
