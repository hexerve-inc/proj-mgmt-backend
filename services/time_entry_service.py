from datetime import datetime, timezone
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
        """Create a manual time entry. Calculates duration from start_at/end_at if provided."""
        # Validate that user exists
        user = self.db.query(User).filter(User.id == entry_in.user_id).first()
        if not user:
            return None
            
        if entry_in.task_id:
            task = self.db.query(Task).filter(Task.id == entry_in.task_id).first()
            if not task:
                return None
        
        data = entry_in.model_dump()
        
        # Calculate duration if start/end provided
        if data.get('start_at') and data.get('end_at'):
            start = data['start_at']
            end = data['end_at']
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            
            delta = end - start
            data['duration'] = max(int(delta.total_seconds() / 60), 0)
        
        # Default date to now if not provided
        if not data.get('date'):
            data['date'] = datetime.now(timezone.utc)
            
        entry = TimeEntry(**data)
        entry.is_running = False  # Manual entries are never running
        
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def start_entry(self, user_id: str, task_id: str, description: Optional[str] = None) -> Optional[TimeEntry]:
        """Start a timer-based activity. Auto-stops any currently running entry for the user."""
        # Validate user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        # Validate task exists
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        # Auto-stop any currently running entry for this user
        running = self.db.query(TimeEntry).filter(
            TimeEntry.user_id == user_id,
            TimeEntry.is_running == True
        ).first()
        if running:
            self._stop_running_entry(running)
        
        now = datetime.now(timezone.utc)
        entry = TimeEntry(
            user_id=user_id,
            task_id=task_id,
            description=description,
            start_at=now,
            date=now,
            is_running=True,
            duration=None,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def stop_entry(self, entry_id: str, user_id: str, description: Optional[str] = None) -> Optional[TimeEntry]:
        """Stop a running timer entry by its ID. Only the owning user can stop it."""
        entry = self.db.query(TimeEntry).filter(
            TimeEntry.id == entry_id,
            TimeEntry.user_id == user_id,
            TimeEntry.is_running == True,
        ).first()
        if not entry:
            return None
        
        if description is not None:
            entry.description = description
        
        self._stop_running_entry(entry)
        return entry

    def stop_active_entry_for_user(self, user_id: str) -> Optional[TimeEntry]:
        """Stop whatever timer is currently running for a given user."""
        entry = self.db.query(TimeEntry).filter(
            TimeEntry.user_id == user_id,
            TimeEntry.is_running == True,
        ).first()
        if not entry:
            return None
        self._stop_running_entry(entry)
        return entry

    def get_active_entry_for_user(self, user_id: str) -> Optional[TimeEntry]:
        """Get the currently running entry for a user, if any."""
        return self.db.query(TimeEntry).filter(
            TimeEntry.user_id == user_id,
            TimeEntry.is_running == True,
        ).first()

    def _stop_running_entry(self, entry: TimeEntry) -> None:
        """Internal: compute duration and mark the entry as stopped."""
        now = datetime.now(timezone.utc)
        entry.end_at = now
        entry.is_running = False
        if entry.start_at:
            # Make start_at timezone-aware if it isn't (db may strip tz info)
            start = entry.start_at
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            delta = now - start
            entry.duration = max(int(delta.total_seconds() / 60), 1)  # At least 1 minute
        else:
            entry.duration = 0
        self.db.commit()
        self.db.refresh(entry)

    def get_entries_for_task(self, task_id: str) -> list[TimeEntry]:
        return self.db.query(TimeEntry).filter(
            TimeEntry.task_id == task_id
        ).order_by(TimeEntry.date.desc()).all()
        
    def get_entries_for_user(self, user_id: str) -> list[TimeEntry]:
        return self.db.query(TimeEntry).filter(
            TimeEntry.user_id == user_id
        ).order_by(TimeEntry.date.desc()).all()
