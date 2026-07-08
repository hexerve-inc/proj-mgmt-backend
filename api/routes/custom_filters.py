from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from api.deps import get_db, get_current_user, require_permission
from models.user import User
from schemas.custom_filter import CustomFilterCreate, CustomFilterUpdate, CustomFilterResponse
from services.custom_filter_service import CustomFilterService

router = APIRouter()

@router.get("/{project_id}/custom-filters", response_model=List[CustomFilterResponse])
def get_custom_filters(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    checker = Depends(require_permission("projects:read"))
):
    checker.check_scope("project", project_id)
    return CustomFilterService.get_project_filters(db, project_id, current_user.id)

@router.post("/{project_id}/custom-filters", response_model=CustomFilterResponse)
def create_custom_filter(
    project_id: str,
    filter_in: CustomFilterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    checker = Depends(require_permission("projects:read"))
):
    checker.check_scope("project", project_id)
    return CustomFilterService.create_filter(db, project_id, current_user.id, filter_in)

@router.patch("/custom-filters/{filter_id}", response_model=CustomFilterResponse)
def update_custom_filter(
    filter_id: str,
    filter_in: CustomFilterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CustomFilterService.update_filter(db, filter_id, current_user.id, filter_in)

@router.delete("/custom-filters/{filter_id}")
def delete_custom_filter(
    filter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    CustomFilterService.delete_filter(db, filter_id, current_user.id)
    return {"message": "Custom filter deleted successfully"}
