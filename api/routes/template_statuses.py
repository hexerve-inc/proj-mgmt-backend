from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import asc

from core.database import get_db
from models.template_status import TemplateStatus
from schemas.template_status import TemplateStatusResponse

router = APIRouter()

# Group sort order matching the service layer
GROUP_ORDER = {
    "OPEN": 0,
    "IN_PROGRESS": 1,
    "ON_HOLD": 2,
    "CLOSED": 3,
}

@router.get("/{template_id}/statuses", response_model=List[TemplateStatusResponse])
def get_template_statuses(template_id: str, db: Session = Depends(get_db)):
    """
    Get all default statuses for a specific template.
    """
    statuses = (
        db.query(TemplateStatus)
        .filter(
            TemplateStatus.template_id == template_id,
            TemplateStatus.deleted_at.is_(None)
        )
        .order_by(asc(TemplateStatus.position))
        .all()
    )
    
    # Sort by group order, then by position
    return sorted(
        statuses,
        key=lambda s: (GROUP_ORDER.get(s.group_key.value, 99), s.position)
    )
