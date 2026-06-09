from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class TaskAttachmentBase(BaseModel):
    file_name: str
    file_size: int
    mime_type: str

class TaskAttachmentCreate(TaskAttachmentBase):
    task_id: str
    cloudinary_public_id: str
    secure_url: str
    uploaded_by_id: Optional[str] = None

class TaskAttachmentRead(TaskAttachmentBase):
    id: str
    task_id: str
    secure_url: str
    uploaded_by_id: Optional[str]
    created_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
