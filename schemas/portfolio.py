from pydantic import BaseModel
from typing import Optional, List

class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None

class PortfolioCreate(PortfolioBase):
    pass

class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PortfolioResponse(PortfolioBase):
    id: str

    class Config:
        from_attributes = True
