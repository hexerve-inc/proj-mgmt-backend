import uuid
from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin
import enum

class RoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    MEMBER = "MEMBER"

class User(SoftDeleteMixin, Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum, name="role_enum"), default=RoleEnum.MEMBER, nullable=False)
    custom_filters = relationship("CustomFilter", back_populates="user", cascade="all, delete-orphan")
