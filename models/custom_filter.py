import uuid
import datetime
from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin

class CustomFilter(SoftDeleteMixin, Base):
    __tablename__ = "custom_filters"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filters = Column(JSON, nullable=False, default=dict)
    sort = Column(JSON, nullable=False, default=dict)
    # created_at, updated_at, deleted_at inherited from SoftDeleteMixin

    project = relationship("Project", back_populates="custom_filters")
    user = relationship("User", back_populates="custom_filters")
