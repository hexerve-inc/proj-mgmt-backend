from pydantic import BaseModel
from typing import Optional
from models.workflow_status import WorkflowGroup


class WorkflowStatusBase(BaseModel):
    name: str
    slug: Optional[str] = None  # Auto-generated from name if not provided
    group_key: WorkflowGroup
    color: Optional[str] = "#6B7280"
    icon: Optional[str] = None
    position: Optional[int] = None
    is_default: Optional[bool] = False


class WorkflowStatusCreate(WorkflowStatusBase):
    pass


class WorkflowStatusUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    group_key: Optional[WorkflowGroup] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    position: Optional[int] = None
    is_default: Optional[bool] = None


class WorkflowStatusResponse(BaseModel):
    id: str
    project_id: str
    name: str
    slug: str
    group_key: WorkflowGroup
    color: str
    icon: Optional[str] = None
    position: int
    is_default: bool

    class Config:
        from_attributes = True


class WorkflowStatusReorderItem(BaseModel):
    id: str
    position: int
    group_key: Optional[WorkflowGroup] = None
