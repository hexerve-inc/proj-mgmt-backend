from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from api.deps import get_db, get_current_user
from schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from services.project_service import ProjectService
from services.notification_service import NotificationService
from services.notification_events import NotificationEvent
from models.notification_preference import NotificationEventType
from models.user import User

router = APIRouter()


def _emit_project_notification(event: NotificationEvent):
    """Background task wrapper — creates its own DB session for async dispatch."""
    from core.database import SessionLocal

    db = SessionLocal()
    try:
        service = NotificationService(db)
        service.emit_sync(event)
    finally:
        db.close()


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
def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)

    # Capture old state for change detection
    old_project = service.get_project(project_id)
    if not old_project:
        raise HTTPException(status_code=404, detail="Project not found")

    old_status = old_project.status.value if old_project.status else None

    project = service.update_project(project_id, project_in)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Emit PROJECT_STATUS_CHANGED if status changed
    update_data = project_in.model_dump(exclude_unset=True)
    if "status" in update_data:
        new_status = update_data["status"]
        if isinstance(new_status, str):
            new_status_str = new_status
        else:
            new_status_str = new_status.value if hasattr(new_status, 'value') else str(new_status)

        if new_status_str != old_status:
            background_tasks.add_task(
                _emit_project_notification,
                NotificationEvent(
                    event_type=NotificationEventType.PROJECT_STATUS_CHANGED,
                    actor_id=current_user.id,
                    entity_id=project_id,
                    entity_type="project",
                    project_id=project_id,
                    metadata={
                        "project_name": project.name,
                        "old_status": old_status or "Unknown",
                        "new_status": new_status_str,
                    },
                ),
            )

    return project

@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    service = ProjectService(db)
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    service.delete_project(project_id)

