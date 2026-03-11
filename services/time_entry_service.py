from sqlalchemy.orm import Session
from models.time_entry import TimeEntry
from models.task import Task
from models.user import User
from schemas.time_entry import TimeEntryCreate
from typing import Optional

class TimeEntryService:
    def __init__(self, db: Session):
        self.db = db

    def log_time(self, entry_in: TimeEntryCreate) -> Optional[TimeEntry]:
        # Validate that user exists
        user = self.db.query(User).filter(User.id == entry_in.user_id).first()
        if not user:
            return None
            
        if entry_in.task_id:
            task = self.db.query(Task).filter(Task.id == entry_in.task_id).first()
            if not task:
                return None
                
        entry = TimeEntry(**entry_in.model_dump())
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def get_entries_for_task(self, task_id: str) -> list[TimeEntry]:
        return self.db.query(TimeEntry).filter(TimeEntry.task_id == task_id).all()
        
    def get_entries_for_user(self, user_id: str) -> list[TimeEntry]:
        return self.db.query(TimeEntry).filter(TimeEntry.user_id == user_id).all()
