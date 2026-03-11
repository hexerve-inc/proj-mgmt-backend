from sqlalchemy.orm import Session
from models.project import Project
from schemas.project import ProjectCreate, ProjectUpdate
from typing import Optional

class ProjectService:
    def __init__(self, db: Session):
        self.db = db
        
    def create_project(self, project_in: ProjectCreate) -> Project:
        project = Project(**project_in.model_dump())
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def get_projects(self) -> list[Project]:
        return self.db.query(Project).all()
        
    def get_project(self, project_id: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def update_project(self, project_id: str, project_in: ProjectUpdate) -> Optional[Project]:
        project = self.get_project(project_id)
        if not project:
            return None
            
        update_data = project_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(project, field, value)
            
        self.db.commit()
        self.db.refresh(project)
        return project
