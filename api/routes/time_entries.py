from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db, get_current_user, require_permission, require_any_permission, get_permission_service
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

@router.get("/", response_model=list[TimeEntryResponse], dependencies=[Depends(require_permission("time_entries:read"))])
def list_time_entries(db: Session = Depends(get_db)):
    service = TimeEntryService(db)
    return service.get_all_entries()

# ── Manual time entry (legacy) ────────────────────────────────────────────

@router.post("/", response_model=TimeEntryResponse)
def log_time(
    entry_in: TimeEntryCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service = Depends(get_permission_service)
):
    from models.task import Task
    task = db.query(Task).filter(Task.id == entry_in.task_id).first()
    if not task:
        raise HTTPException(status_code=400, detail="Invalid Task ID")
    perm_service.check_permission(current_user.id, "time_entries:create", "project", task.project_id)
    
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
    perm_service = Depends(get_permission_service)
):
    """Start a timer for the authenticated user on a given task."""
    from models.task import Task
    task = db.query(Task).filter(Task.id == request.task_id).first()
    if not task:
        raise HTTPException(status_code=400, detail="Invalid Task ID")
    perm_service.check_permission(current_user.id, "time_entries:create", "project", task.project_id)

    service = TimeEntryService(db)
    entry = service.start_entry(
        user_id=current_user.id,
        task_id=request.task_id,
        description=request.description,
    )
    if not entry:
        raise HTTPException(status_code=400, detail="Failed to start entry")
    return entry

@router.post("/stop/{entry_id}", response_model=TimeEntryResponse, dependencies=[Depends(require_any_permission("time_entries:update_own", "time_entries:update"))])
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

@router.get("/task/{task_id}", response_model=list[TimeEntryResponse], dependencies=[Depends(require_any_permission("time_entries:read", "time_entries:read_own"))])
def get_task_entries(
    task_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service = Depends(get_permission_service)
):
    from models.task import Task
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    has_read = perm_service.has_permission(current_user.id, "time_entries:read", "project", task.project_id)
    if not has_read:
        perm_service.check_permission(current_user.id, "time_entries:read_own", "project", task.project_id)

    service = TimeEntryService(db)
    entries = service.get_entries_for_task(task_id)
    if not has_read:
        entries = [e for e in entries if e.user_id == current_user.id]
    return entries

@router.get("/user/{user_id}", response_model=list[TimeEntryResponse])
def get_user_entries(
    user_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service = Depends(get_permission_service)
):
    if user_id != current_user.id:
        perm_service.check_permission(current_user.id, "time_entries:read")
    service = TimeEntryService(db)
    return service.get_entries_for_user(user_id)

# ── Single entry CRUD ────────────────────────────────────────────────────

@router.get("/{entry_id}", response_model=TimeEntryResponse, dependencies=[Depends(require_any_permission("time_entries:read", "time_entries:read_own"))])
def get_time_entry(
    entry_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service = Depends(get_permission_service)
):
    """Get a single time entry by ID."""
    service = TimeEntryService(db)
    entry = service.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
        
    has_read = perm_service.has_permission(current_user.id, "time_entries:read", "project", entry.task.project_id)
    if not has_read and entry.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
        
    return entry

@router.patch("/{entry_id}", response_model=TimeEntryResponse, dependencies=[Depends(require_any_permission("time_entries:update_own", "time_entries:update"))])
def update_time_entry(
    entry_id: str,
    updates: TimeEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service = Depends(get_permission_service)
):
    """Update a time entry."""
    service = TimeEntryService(db)
    entry = service.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
        
    # Wait, the matrix only has time_entries:update_own for dev/qa, and none for update others.
    # We will assume project admins can update. But let's check update_own first.
    if entry.user_id != current_user.id:
        perm_service.check_permission(current_user.id, "time_entries:update", "project", entry.task.project_id)
        
    entry = service.update_entry(entry_id, updates.model_dump(exclude_unset=True))
    return entry

@router.delete("/{entry_id}")
def delete_time_entry(
    entry_id: str, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service = Depends(get_permission_service)
):
    """Soft-delete a time entry."""
    service = TimeEntryService(db)
    entry = service.get_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")
        
    perm_service.check_permission(current_user.id, "time_entries:delete", "project", entry.task.project_id)
    
    success = service.delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Time entry not found")
    return {"detail": "Time entry deleted"}

