from pydantic import BaseModel
from typing import Optional

class ProgramBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProgramCreate(ProgramBase):
    pass

class ProgramUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProgramResponse(ProgramBase):
    id: str

    class Config:
        from_attributes = True
