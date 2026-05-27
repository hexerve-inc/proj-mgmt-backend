from datetime import date
from pydantic import BaseModel
from typing import Optional
from models.task import Priority
from schemas.user import UserResponse
from schemas.workflow_status import WorkflowStatusResponse
from schemas.label import LabelResponse


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status_id: Optional[str] = None
    priority: Optional[Priority] = Priority.MEDIUM
    progress: Optional[int] = 0
    story_points: Optional[int] = 0
    assignee_id: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    sprint_id: Optional[str] = None
    is_milestone: Optional[bool] = False
    task_type: Optional[str] = "task"
    parent_id: Optional[str] = None


class TaskCreate(TaskBase):
    project_id: str
    label_ids: Optional[list[str]] = None
    group_id: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status_id: Optional[str] = None
    priority: Optional[Priority] = None
    progress: Optional[int] = None
    story_points: Optional[int] = None
    assignee_id: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    sprint_id: Optional[str] = None
    label_ids: Optional[list[str]] = None
    group_id: Optional[str] = None
    is_milestone: Optional[bool] = None
    task_type: Optional[str] = None
    parent_id: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    task_code: Optional[str] = None
    title: str
    description: Optional[str] = None
    status_id: str
    status: Optional[WorkflowStatusResponse] = None
    priority: Optional[Priority] = None
    progress: Optional[int] = 0
    story_points: Optional[int] = 0
    project_id: str
    assignee_id: Optional[str] = None
    assignee: Optional[UserResponse] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    sprint_id: Optional[str] = None
    labels: list[LabelResponse] = []
    group_id: Optional[str] = None
    is_milestone: Optional[bool] = False
    task_type: Optional[str] = "task"
    parent_id: Optional[str] = None

    class Config:
        from_attributes = True
