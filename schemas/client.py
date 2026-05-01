from pydantic import BaseModel, EmailStr
from typing import Optional

class ClientBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    type: Optional[str] = "external"
    address: Optional[str] = None
    notes: Optional[str] = None
    industry: Optional[str] = None

class ClientCreate(ClientBase):
    pass

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    industry: Optional[str] = None

class ClientResponse(ClientBase):
    id: str

    class Config:
        from_attributes = True
