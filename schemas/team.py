from pydantic import BaseModel
from typing import Optional, List
from schemas.user import UserResponse

class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    capacity: Optional[int] = 40
    velocity: Optional[int] = 0

class TeamCreate(TeamBase):
    project_manager_id: Optional[str] = None
    lead_id: Optional[str] = None
    product_manager_id: Optional[str] = None
    member_ids: Optional[List[str]] = []
    project_ids: Optional[List[str]] = []

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    capacity: Optional[int] = None
    velocity: Optional[int] = None
    project_manager_id: Optional[str] = None
    lead_id: Optional[str] = None
    product_manager_id: Optional[str] = None
    member_ids: Optional[List[str]] = None
    project_ids: Optional[List[str]] = None

class TeamResponse(TeamBase):
    id: str
    project_manager: Optional[UserResponse] = None
    lead: Optional[UserResponse] = None
    product_manager: Optional[UserResponse] = None
    members: List[UserResponse] = []
    project_ids: List[str] = []

    class Config:
        from_attributes = True
