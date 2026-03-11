from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TimeEntryBase(BaseModel):
    duration: int
    description: Optional[str] = None
    task_id: Optional[str] = None

class TimeEntryCreate(TimeEntryBase):
    user_id: str

class TimeEntryUpdate(BaseModel):
    duration: Optional[int] = None
    description: Optional[str] = None
    task_id: Optional[str] = None

class TimeEntryResponse(TimeEntryBase):
    id: str
    date: datetime
    user_id: str

    class Config:
        from_attributes = True
