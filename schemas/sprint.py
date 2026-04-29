from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class SprintBase(BaseModel):
    name: str
    goal: Optional[str] = None
    status: Optional[str] = "active"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    velocity: Optional[int] = 0
    project_id: Optional[str] = None


class SprintCreate(SprintBase):
    pass

class SprintUpdate(SprintBase):
    name: Optional[str] = None

class SprintResponse(SprintBase):
    id: str

    class Config:
        from_attributes = True
