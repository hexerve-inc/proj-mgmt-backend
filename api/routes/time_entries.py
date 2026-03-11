from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
from schemas.time_entry import TimeEntryCreate, TimeEntryResponse
from services.time_entry_service import TimeEntryService

router = APIRouter()

@router.post("/", response_model=TimeEntryResponse)
def log_time(entry_in: TimeEntryCreate, db: Session = Depends(get_db)):
    service = TimeEntryService(db)
    entry = service.log_time(entry_in)
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid User or Task ID")
    return entry

@router.get("/task/{task_id}", response_model=list[TimeEntryResponse])
def get_task_entries(task_id: str, db: Session = Depends(get_db)):
    service = TimeEntryService(db)
    return service.get_entries_for_task(task_id)

@router.get("/user/{user_id}", response_model=list[TimeEntryResponse])
def get_user_entries(user_id: str, db: Session = Depends(get_db)):
    service = TimeEntryService(db)
    return service.get_entries_for_user(user_id)
