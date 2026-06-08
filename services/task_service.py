import uuid
from sqlalchemy.orm import Session, joinedload
from models.task import Task
from models.label import Label
from models.task_group import TaskGroup
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
            .filter(Task.deleted_at.is_(None))
            .options(joinedload(Task.assignee), joinedload(Task.status), joinedload(Task.labels))
            .all()
        )

    def create_task(self, task_in: TaskCreate) -> Task:
        task_data = task_in.model_dump()
        label_ids = task_data.pop("label_ids", None)
        group_id = task_data.pop("group_id", None)
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
        if group_id:
            task.group_id = group_id

        # Attach labels if provided (validate project scope)
        if label_ids:
            labels = self.db.query(Label).filter(Label.id.in_(label_ids)).all()
            if len(labels) != len(label_ids):
                raise ValueError("One or more labels not found")
            for lbl in labels:
                if lbl.project_id and lbl.project_id != task_in.project_id:
                    raise ValueError("Label does not belong to the task's project")
            task.labels = labels

        self.db.add(task)
        self.db.commit()
        return self.get_task(task.id)

    def get_tasks_for_project(self, project_id: str) -> list[Task]:
        return (
            self.db.query(Task)
            .filter(Task.project_id == project_id, Task.deleted_at.is_(None))
            .options(joinedload(Task.assignee), joinedload(Task.status), joinedload(Task.labels))
            .all()
        )

    def get_task(self, task_id: str) -> Optional[Task]:
        return (
            self.db.query(Task)
            .filter(Task.id == task_id, Task.deleted_at.is_(None))
            .options(joinedload(Task.assignee), joinedload(Task.status), joinedload(Task.labels))
            .first()
        )

    def update_task(self, task_id: str, task_in: TaskUpdate) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None
            
        update_data = task_in.model_dump(exclude_unset=True)
        label_ids = update_data.pop("label_ids", None)
        group_id = update_data.pop("group_id", None)

        for field, value in update_data.items():
            setattr(task, field, value)

        if group_id is not None:
            task.group_id = group_id

        if label_ids is not None:
            # replace labels set
            labels = self.db.query(Label).filter(Label.id.in_(label_ids)).all()
            if len(labels) != len(label_ids):
                raise ValueError("One or more labels not found")
            # optional: validate project scope
            for lbl in labels:
                if lbl.project_id and lbl.project_id != task.project_id:
                    raise ValueError("Label does not belong to the task's project")
            task.labels = labels

        self.db.commit()
        return self.get_task(task_id)

    def delete_task(self, task_id: str) -> bool:
        """Soft-delete a task by setting deleted_at."""
        task = self.get_task(task_id)
        if not task:
            return False
        import datetime
        suffix = f"-del-{int(datetime.datetime.now().timestamp())}"
        task.task_code = f"{task.task_code}{suffix}"
        task.soft_delete()
        self.db.commit()
        return True
