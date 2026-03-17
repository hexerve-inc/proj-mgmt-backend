from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from schemas.sprint import SprintCreate, SprintUpdate, SprintResponse
from services.sprint_service import SprintService
from api.deps import get_current_user
from models.user import User

router = APIRouter()

@router.get("/", response_model=List[SprintResponse])
def get_sprints(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SprintService.get_all(db)

@router.post("/", response_model=SprintResponse)
def create_sprint(sprint: SprintCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return SprintService.create(db, sprint)

@router.get("/{sprint_id}", response_model=SprintResponse)
def get_sprint(sprint_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_sprint = SprintService.get_by_id(db, sprint_id)
    if not db_sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return db_sprint

@router.put("/{sprint_id}", response_model=SprintResponse)
def update_sprint(sprint_id: str, sprint: SprintUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_sprint = SprintService.update(db, sprint_id, sprint)
    if not db_sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return db_sprint

@router.delete("/{sprint_id}")
def delete_sprint(sprint_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not SprintService.delete(db, sprint_id):
        raise HTTPException(status_code=404, detail="Sprint not found")
    return {"message": "Sprint deleted"}

