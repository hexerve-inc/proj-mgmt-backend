import uuid
from sqlalchemy.orm import Session, joinedload
from models.task import Task
from models.project import Project
from schemas.task import TaskCreate, TaskUpdate
from services.workflow_status_service import WorkflowStatusService
from typing import Optional


class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def generate_task_code(self, project_id: str) -> str:
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return f"TSK-{uuid.uuid4().hex[:6].upper()}"
            
        project.task_count += 1
        self.db.add(project)
        return f"{project.project_key}-{project.task_count}"

    def get_tasks(self) -> list[Task]:
        return (
            self.db.query(Task)
            .options(joinedload(Task.assignee), joinedload(Task.status))
            .all()
        )

    def create_task(self, task_in: TaskCreate) -> Task:
        task_data = task_in.model_dump()
        task_code = self.generate_task_code(task_in.project_id)

        # Resolve default status if none provided
        if not task_data.get("status_id"):
            ws_service = WorkflowStatusService(self.db)
            default_status = ws_service.get_default_status(task_in.project_id)
            if default_status:
                task_data["status_id"] = default_status.id
            else:
                raise ValueError(
                    "No default workflow status configured for this project."
                )

        task = Task(**task_data, task_code=task_code)
        self.db.add(task)
        self.db.commit()
        return self.get_task(task.id)

    def get_tasks_for_project(self, project_id: str) -> list[Task]:
        return (
            self.db.query(Task)
            .filter(Task.project_id == project_id)
            .options(joinedload(Task.assignee), joinedload(Task.status))
            .all()
        )

    def get_task(self, task_id: str) -> Optional[Task]:
        return (
            self.db.query(Task)
            .filter(Task.id == task_id)
            .options(joinedload(Task.assignee), joinedload(Task.status))
            .first()
        )

    def update_task(self, task_id: str, task_in: TaskUpdate) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None
            
        update_data = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
            
        self.db.commit()
        return self.get_task(task_id)
