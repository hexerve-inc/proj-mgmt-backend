from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TimeEntryBase(BaseModel):
    duration: Optional[int] = None
    description: Optional[str] = None
    task_id: Optional[str] = None

class TimeEntryCreate(TimeEntryBase):
    """Schema for manual time entry creation."""
    user_id: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    duration: Optional[int] = None  # Optional, can be calculated from start/end

class TimeEntryUpdate(BaseModel):
    duration: Optional[int] = None
    description: Optional[str] = None
    task_id: Optional[str] = None

class TimeEntryStartRequest(BaseModel):
    """Schema for starting a timer-based activity."""
    task_id: str
    description: Optional[str] = None

class TimeEntryStopRequest(BaseModel):
    """Schema for stopping a timer-based activity (optional description update)."""
    description: Optional[str] = None

class TimeEntryResponse(BaseModel):
    id: str
    duration: Optional[int] = None
    date: datetime
    description: Optional[str] = None
    task_id: Optional[str] = None
    user_id: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_running: bool = False

    class Config:
        from_attributes = True
