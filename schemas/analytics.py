from pydantic import BaseModel
from typing import Optional
from datetime import date


class UserTaskMetric(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    total_tasks: int = 0
    completed_tasks: int = 0
    active_tasks: int = 0
    overdue_tasks: int = 0


class ProjectTaskMetric(BaseModel):
    project_id: str
    project_name: str
    project_key: str
    total_tasks: int = 0
    completed_tasks: int = 0
    active_tasks: int = 0
    overdue_tasks: int = 0
    completion_percentage: float = 0.0


class DueDateTask(BaseModel):
    task_id: str
    task_code: Optional[str] = None
    title: str
    assignee_name: Optional[str] = None
    assignee_id: Optional[str] = None
    project_name: str
    project_id: str
    priority: Optional[str] = None
    status_group: Optional[str] = None
    status_name: Optional[str] = None
    due_date: Optional[date] = None

    class Config:
        from_attributes = True


class UserWorkload(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    active_task_count: int = 0


class AnalyticsSummary(BaseModel):
    total_users: int = 0
    users_with_no_active_tasks: int = 0
    avg_active_tasks_per_user: float = 0.0
    total_projects: int = 0
    active_projects: int = 0
    completed_projects: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    tasks_in_progress: int = 0
