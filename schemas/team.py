from pydantic import BaseModel
from typing import Optional

class TeamBase(BaseModel):
    name: str

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    name: Optional[str] = None

class TeamResponse(TeamBase):
    id: str

    class Config:
        from_attributes = True
