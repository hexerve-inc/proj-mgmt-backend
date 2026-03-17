from pydantic import BaseModel
from typing import Optional
from models.task import TaskStatus, Priority

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    progress: int = 0
    assignee_id: Optional[str] = None

class TaskCreate(TaskBase):
    project_id: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    progress: Optional[int] = None
    assignee_id: Optional[str] = None

class TaskResponse(TaskBase):
    id: str
    task_code: str
    project_id: str

    class Config:
        from_attributes = True
