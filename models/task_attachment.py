import uuid
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin

class TaskAttachment(SoftDeleteMixin, Base):
    __tablename__ = "task_attachments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    cloudinary_public_id = Column(String, nullable=False)
    secure_url = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    uploaded_by_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    task = relationship("Task", back_populates="attachments")
    uploaded_by = relationship("User")
