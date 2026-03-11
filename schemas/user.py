from pydantic import BaseModel, EmailStr
from models.user import RoleEnum

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: RoleEnum = RoleEnum.MEMBER

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: str

    class Config:
        from_attributes = True
