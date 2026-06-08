from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from schemas.sprint import SprintCreate, SprintUpdate, SprintResponse
from services.sprint_service import SprintService
from services.notification_service import NotificationService
from services.notification_events import NotificationEvent
from models.notification_preference import NotificationEventType
from api.deps import get_current_user
from models.user import User

router = APIRouter()


def _emit_sprint_notification(event: NotificationEvent):
    """Background task wrapper — creates its own DB session for async dispatch."""
    from core.database import SessionLocal

    db = SessionLocal()
    try:
        service = NotificationService(db)
        service.emit_sync(event)
    finally:
        db.close()


@router.get("/", response_model=List[SprintResponse])
def get_sprints(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SprintService.get_all(db)

@router.post("/", response_model=SprintResponse)
def create_sprint(sprint: SprintCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SprintService.create(db, sprint)

@router.get("/{sprint_id}", response_model=SprintResponse)
def get_sprint(sprint_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_sprint = SprintService.get_by_id(db, sprint_id)
    if not db_sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return db_sprint

@router.put("/{sprint_id}", response_model=SprintResponse)
def update_sprint(
    sprint_id: str,
    sprint: SprintUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Capture old state for change detection
    old_sprint = SprintService.get_by_id(db, sprint_id)
    if not old_sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    old_status = old_sprint.status
    project_id = old_sprint.project_id

    db_sprint = SprintService.update(db, sprint_id, sprint)
    if not db_sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    # Emit sprint lifecycle events based on status transitions
    update_data = sprint.model_dump(exclude_unset=True)
    new_status = update_data.get("status")

    if new_status and new_status != old_status and project_id:
        if new_status == "active":
            background_tasks.add_task(
                _emit_sprint_notification,
                NotificationEvent(
                    event_type=NotificationEventType.SPRINT_STARTED,
                    actor_id=current_user.id,
                    entity_id=sprint_id,
                    entity_type="sprint",
                    project_id=project_id,
                    metadata={
                        "sprint_name": db_sprint.name,
                        "sprint_goal": db_sprint.goal or "",
                    },
                ),
            )
        elif new_status == "completed":
            background_tasks.add_task(
                _emit_sprint_notification,
                NotificationEvent(
                    event_type=NotificationEventType.SPRINT_COMPLETED,
                    actor_id=current_user.id,
                    entity_id=sprint_id,
                    entity_type="sprint",
                    project_id=project_id,
                    metadata={
                        "sprint_name": db_sprint.name,
                    },
                ),
            )

    return db_sprint

@router.delete("/{sprint_id}")
def delete_sprint(sprint_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not SprintService.delete(db, sprint_id):
        raise HTTPException(status_code=404, detail="Sprint not found")
    return {"message": "Sprint deleted"}

