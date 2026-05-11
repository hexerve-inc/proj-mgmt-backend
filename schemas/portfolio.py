from pydantic import BaseModel
from typing import Optional, List

class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    program_ids: Optional[List[str]] = None

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    program_ids: Optional[List[str]] = None

from schemas.program import ProgramResponse

class PortfolioResponse(PortfolioBase):
    id: str
    programs: List[ProgramResponse] = []

    class Config:
        from_attributes = True
