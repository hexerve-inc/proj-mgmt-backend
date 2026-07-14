from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from models.project import Project
from schemas.project import ProjectCreate, ProjectUpdate
from services.workflow_status_service import WorkflowStatusService
from typing import Optional
import re

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        
    def create_project(self, project_in: ProjectCreate, actor_id: Optional[str] = None) -> Project:
        normalized_name = project_in.name.strip()
        normalized_key = self._normalize_project_key(project_in.project_key, normalized_name)

        existing_name = (
            self.db.query(Project)
            .filter(func.lower(Project.name) == normalized_name.lower(), Project.deleted_at.is_(None))
            .first()
        )
        if existing_name:
            raise ValueError("Project name already exists. Please choose a different project name.")

        existing_key = (
            self.db.query(Project)
            .filter(func.lower(Project.project_key) == normalized_key.lower(), Project.deleted_at.is_(None))
            .first()
        )
        if existing_key:
            raise ValueError("Project key already exists. Please choose a different project key.")

        project_payload = project_in.model_dump()
        project_payload["name"] = normalized_name
        project_payload["project_key"] = normalized_key
        project_payload["created_by_id"] = actor_id

        project = Project(**project_payload)
        self.db.add(project)

        try:
            self.db.flush()
            ws_service = WorkflowStatusService(self.db)
            ws_service.seed_defaults(project.id)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise ValueError(
                "Project name or key already exists. Please choose a different project name or key."
            )

        self.db.refresh(project)

        return project

    def get_projects(self) -> list[Project]:
        return self.db.query(Project).filter(Project.deleted_at.is_(None)).all()
        
    def get_project(self, project_id: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id, Project.deleted_at.is_(None)).first()

    def update_project(self, project_id: str, project_in: ProjectUpdate) -> Optional[Project]:
        project = self.get_project(project_id)
        if not project:
            return None
            
        update_data = project_in.model_dump(exclude_unset=True)
        # Never allow name or project_key to be changed via update
        update_data.pop("name", None)
        update_data.pop("project_key", None)
        for field, value in update_data.items():
            setattr(project, field, value)
            
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: str) -> None:
        project = self.get_project(project_id)
        if project:
            import datetime
            suffix = f"-del-{int(datetime.datetime.now().timestamp())}"
            project.name = f"{project.name}{suffix}"
            project.project_key = f"{project.project_key}{suffix}"
            project.soft_delete()
            self.db.commit()

    def check_uniqueness(self, name: Optional[str] = None, project_key: Optional[str] = None) -> dict:
        result = {"nameExists": False, "keyExists": False}
        if name and name.strip():
            normalized_name = name.strip()
            existing_name = (
                self.db.query(Project)
                .filter(func.lower(Project.name) == normalized_name.lower(), Project.deleted_at.is_(None))
                .first()
            )
            if existing_name:
                result["nameExists"] = True
                
        if project_key and project_key.strip():
            normalized_key = project_key.strip()
            existing_key = (
                self.db.query(Project)
                .filter(func.lower(Project.project_key) == normalized_key.lower(), Project.deleted_at.is_(None))
                .first()
            )
            if existing_key:
                result["keyExists"] = True
                
        return result

    @staticmethod
    def _normalize_project_key(project_key: Optional[str], project_name: str) -> str:
        if project_key and project_key.strip():
            return project_key.strip()

        generated_key = re.sub(r"[^A-Za-z0-9]+", "-", project_name).strip("-").upper()
        return generated_key or "PRJ"
