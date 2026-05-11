from datetime import date
from pydantic import BaseModel
from typing import Optional
from models.task import TaskStatus, Priority
from schemas.user import UserResponse

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: Optional[TaskStatus] = TaskStatus.TODO
    priority: Optional[Priority] = Priority.MEDIUM
    progress: Optional[int] = 0
    story_points: Optional[int] = 0
    assignee_id: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    sprint_id: Optional[str] = None

class TaskCreate(TaskBase):
    project_id: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    progress: Optional[int] = None
    story_points: Optional[int] = None
    assignee_id: Optional[str] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    sprint_id: Optional[str] = None

class TaskResponse(TaskBase):
    id: str
    task_code: Optional[str] = None
    project_id: str
    assignee: Optional[UserResponse] = None

    class Config:
        from_attributes = True
