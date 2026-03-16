import uuid
from sqlalchemy.orm import Session
from models.task import Task
from models.project import Project
from schemas.task import TaskCreate, TaskUpdate
from typing import Optional

class TaskService:
    def __init__(self, db: Session):
        self.db = db

    def generate_task_code(self, project_id: str) -> str:
        # A generation strategy for task codes based on project id prefix + uuid
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            prefix = "TSK"
        else:
            # Using the first 3 letters of the project name as a prefix, fallback to TSK
            prefix = project.name[:3].upper() if project.name else "TSK"
            
        short_id = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{short_id}"

    def get_tasks(self) -> list[Task]:
        return self.db.query(Task).all()

    def create_task(self, task_in: TaskCreate) -> Task:
        task_code = self.generate_task_code(task_in.project_id)
        task = Task(**task_in.model_dump(), task_code=task_code)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_tasks_for_project(self, project_id: str) -> list[Task]:
        return self.db.query(Task).filter(Task.project_id == project_id).all()

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.db.query(Task).filter(Task.id == task_id).first()

    def update_task(self, task_id: str, task_in: TaskUpdate) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None
            
        update_data = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
            
        self.db.commit()
        self.db.refresh(task)
        return task
