from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db, get_current_user
from schemas.time_entry import (
    TimeEntryCreate,
    TimeEntryResponse,
    TimeEntryStartRequest,
    TimeEntryStopRequest,
)
from services.time_entry_service import TimeEntryService
from models.user import User

router = APIRouter()

# ── Manual time entry (legacy) ────────────────────────────────────────────

@router.post("/", response_model=TimeEntryResponse)
def log_time(entry_in: TimeEntryCreate, db: Session = Depends(get_db)):
    service = TimeEntryService(db)
    entry = service.log_time(entry_in)
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid User or Task ID")
    return entry

# ── Timer-based activity endpoints ────────────────────────────────────────

@router.post("/start", response_model=TimeEntryResponse)
def start_activity(
    request: TimeEntryStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a timer for the authenticated user on a given task.
    Auto-stops any previously running timer for this user."""
    service = TimeEntryService(db)
    entry = service.start_entry(
        user_id=current_user.id,
        task_id=request.task_id,
        description=request.description,
    )
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid Task ID")
    return entry

@router.post("/stop/{entry_id}", response_model=TimeEntryResponse)
def stop_activity(
    entry_id: str,
    request: TimeEntryStopRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop a specific running timer entry."""
    service = TimeEntryService(db)
    desc = request.description if request else None
    entry = service.stop_entry(entry_id, current_user.id, description=desc)
    if not entry:
        raise HTTPException(status_code=404, detail="No running entry found with this ID for the current user")
    return entry

@router.post("/stop", response_model=TimeEntryResponse)
def stop_current_activity(
    request: TimeEntryStopRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stop whatever timer is currently running for the authenticated user."""
    service = TimeEntryService(db)
    desc = request.description if request else None
    # If description provided, apply it
    entry = service.stop_active_entry_for_user(current_user.id)
    if not entry:
        raise HTTPException(status_code=404, detail="No running activity found")
    if desc is not None:
        entry.description = desc
        db.commit()
        db.refresh(entry)
    return entry

@router.get("/active", response_model=TimeEntryResponse)
def get_active_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the currently running timer for the authenticated user, if any."""
    service = TimeEntryService(db)
    entry = service.get_active_entry_for_user(current_user.id)
    if not entry:
        raise HTTPException(status_code=404, detail="No active activity")
    return entry

# ── Query endpoints ──────────────────────────────────────────────────────

@router.get("/task/{task_id}", response_model=list[TimeEntryResponse])
def get_task_entries(task_id: str, db: Session = Depends(get_db)):
    service = TimeEntryService(db)
    return service.get_entries_for_task(task_id)

@router.get("/user/{user_id}", response_model=list[TimeEntryResponse])
def get_user_entries(user_id: str, db: Session = Depends(get_db)):
    service = TimeEntryService(db)
    return service.get_entries_for_user(user_id)
