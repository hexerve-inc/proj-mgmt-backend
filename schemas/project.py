from datetime import date
from pydantic import AliasChoices, BaseModel, Field, field_validator
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

    @field_validator("status", mode="before")
    def map_status(cls, v):
        if isinstance(v, str):
            v_upper = v.upper().replace("-", "_")
            if v_upper in [e.value for e in ProjectStatus]:
                return v_upper
            if v_upper == "CANCELLED":
                return ProjectStatus.COMPLETED.value # Map cancelled to completed for backend
        return v

class ProjectCreate(ProjectBase):
    project_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("project_key", "key"),
    )
    template_id: Optional[str] = None
    custom_statuses: Optional[list[dict]] = None


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

    @field_validator("status", mode="before")
    def map_status(cls, v):
        if isinstance(v, str):
            v_upper = v.upper().replace("-", "_")
            if v_upper in [e.value for e in ProjectStatus]:
                return v_upper
            if v_upper == "CANCELLED":
                return ProjectStatus.COMPLETED.value
        return v

class ProjectResponse(ProjectBase):
    id: str
    project_key: str
    task_count: int
    template_id: Optional[str] = None

    class Config:
        from_attributes = True
