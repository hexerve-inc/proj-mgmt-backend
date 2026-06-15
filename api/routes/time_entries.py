from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db, get_current_user
from schemas.time_entry import (
    TimeEntryCreate,
    TimeEntryUpdate,
    TimeEntryResponse,
    TimeEntryStartRequest,
    TimeEntryStopRequest,
)
from services.time_entry_service import TimeEntryService
from models.user import User

router = APIRouter()

# ── List all time entries ─────────────────────────────────────────────────

@router.get("/", response_model=list[TimeEntryResponse])
def list_time_entries(db: Session = Depends(get_db)):
    service = TimeEntryService(db)
    return service.get_all_entries()

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

# ── Single entry CRUD ────────────────────────────────────────────────────

@router.get("/{entry_id}", response_model=TimeEntryResponse)
def get_time_entry(entry_id: str, db: Session = Depends(get_db)):
    """Get a single time entry by ID."""
    service = TimeEntryService(db)
    entry = service.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return entry

@router.patch("/{entry_id}", response_model=TimeEntryResponse)
def update_time_entry(
    entry_id: str,
    updates: TimeEntryUpdate,
    db: Session = Depends(get_db),
):
    """Update a time entry."""
    service = TimeEntryService(db)
    entry = service.update_entry(entry_id, updates.model_dump(exclude_unset=True))
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return entry

@router.delete("/{entry_id}")
def delete_time_entry(entry_id: str, db: Session = Depends(get_db)):
    """Soft-delete a time entry."""
    service = TimeEntryService(db)
    success = service.delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return {"detail": "Time entry deleted"}

