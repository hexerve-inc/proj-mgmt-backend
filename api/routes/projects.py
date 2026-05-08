from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
from schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from services.project_service import ProjectService

router = APIRouter()

@router.post("/", response_model=ProjectResponse)
def create_project(project_in: ProjectCreate, db: Session = Depends(get_db)):
    service = ProjectService(db)
    try:
        return service.create_project(project_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@router.get("/", response_model=list[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.get_projects()

@router.get("/validate", response_model=dict)
def validate_project(name: str = None, project_key: str = None, db: Session = Depends(get_db)):
    service = ProjectService(db)
    return service.check_uniqueness(name, project_key)

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, project_in: ProjectUpdate, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.update_project(project_id, project_in)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    service.delete_project(project_id)

