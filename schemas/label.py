from pydantic import BaseModel
from typing import Optional

class LabelBase(BaseModel):
    name: str
    color: Optional[str] = "#94a3b8"
    project_id: Optional[str] = None

class LabelCreate(LabelBase):
    pass

class LabelResponse(LabelBase):
    id: str

    class Config:
        from_attributes = True
