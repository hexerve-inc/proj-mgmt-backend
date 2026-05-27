from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class CustomFilterBase(BaseModel):
    name: str
    filters: Dict[str, Any] = {}
    sort: Dict[str, Any] = {}

class CustomFilterCreate(CustomFilterBase):
    pass

class CustomFilterUpdate(BaseModel):
    name: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    sort: Optional[Dict[str, Any]] = None

class CustomFilterResponse(CustomFilterBase):
    id: str
    project_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
