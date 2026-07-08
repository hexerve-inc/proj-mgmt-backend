from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from core.database import get_db
from models.task_attachment import TaskAttachment
from models.task import Task
from models.user import User
from schemas.task_attachment import TaskAttachmentRead
from services.cloudinary_service import CloudinaryService
from api.deps import get_current_user, get_permission_service

router = APIRouter(prefix="/tasks/{task_id}/attachments", tags=["task-attachments"])

@router.post("", response_model=TaskAttachmentRead, status_code=status.HTTP_201_CREATED)
def upload_task_attachment(
    task_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service = Depends(get_permission_service)
):
    # Verify task exists
    task = db.query(Task).filter(Task.id == task_id, Task.deleted_at.is_(None)).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    perm_service.check_permission(current_user.id, "attachments:upload", "project", task.project_id)

    # Upload to Cloudinary
    try:
        upload_result = CloudinaryService.upload_file(file, folder=f"pmtool/tasks/{task_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")

    if not upload_result.get("secure_url") or not upload_result.get("public_id"):
        raise HTTPException(status_code=500, detail="Failed to retrieve URL from Cloudinary")

    # Create TaskAttachment record
    attachment = TaskAttachment(
        task_id=task_id,
        cloudinary_public_id=upload_result["public_id"],
        secure_url=upload_result["secure_url"],
        file_name=file.filename,
        file_size=file.size or 0,
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by_id=current_user.id
    )
    
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment

@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task_attachment(
    task_id: str,
    attachment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    perm_service = Depends(get_permission_service)
):
    attachment = db.query(TaskAttachment).filter(
        TaskAttachment.id == attachment_id,
        TaskAttachment.task_id == task_id,
        TaskAttachment.deleted_at.is_(None)
    ).first()
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    perm_service.check_permission(current_user.id, "attachments:delete", "project", attachment.task.project_id)

    # Delete from Cloudinary
    try:
        CloudinaryService.delete_file(attachment.cloudinary_public_id)
    except Exception as e:
        # We might want to still delete the DB record even if Cloudinary fails,
        # but let's log or raise it for now.
        raise HTTPException(status_code=500, detail=f"Failed to delete file from Cloudinary: {str(e)}")

    # Soft delete in DB
    db.delete(attachment)
    db.commit()
    return None
