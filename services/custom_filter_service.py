from sqlalchemy.orm import Session
from models.custom_filter import CustomFilter
from schemas.custom_filter import CustomFilterCreate, CustomFilterUpdate
from fastapi import HTTPException

class CustomFilterService:
    @staticmethod
    def get_project_filters(db: Session, project_id: str, user_id: str):
        return db.query(CustomFilter).filter(
            CustomFilter.project_id == project_id,
            CustomFilter.user_id == user_id,
            CustomFilter.deleted_at.is_(None),
        ).all()

    @staticmethod
    def get_filter(db: Session, filter_id: str, user_id: str):
        db_filter = db.query(CustomFilter).filter(
            CustomFilter.id == filter_id,
            CustomFilter.user_id == user_id,
            CustomFilter.deleted_at.is_(None),
        ).first()
        if not db_filter:
            raise HTTPException(status_code=404, detail="Custom filter not found")
        return db_filter

    @staticmethod
    def create_filter(db: Session, project_id: str, user_id: str, filter_in: CustomFilterCreate):
        db_filter = CustomFilter(
            name=filter_in.name,
            project_id=project_id,
            user_id=user_id,
            filters=filter_in.filters,
            sort=filter_in.sort
        )
        db.add(db_filter)
        db.commit()
        db.refresh(db_filter)
        return db_filter

    @staticmethod
    def update_filter(db: Session, filter_id: str, user_id: str, filter_in: CustomFilterUpdate):
        db_filter = CustomFilterService.get_filter(db, filter_id, user_id)
        update_data = filter_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_filter, key, value)
        db.commit()
        db.refresh(db_filter)
        return db_filter

    @staticmethod
    def delete_filter(db: Session, filter_id: str, user_id: str):
        db_filter = CustomFilterService.get_filter(db, filter_id, user_id)
        db_filter.soft_delete()
        db.commit()
        return True
