from pydantic import BaseModel
from typing import Optional

class ProgramBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProgramCreate(ProgramBase):
    portfolio_id: Optional[str] = None
    project_ids: Optional[list[str]] = None

class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProgramResponse(ProgramBase):
    id: str

    class Config:
        from_attributes = True
