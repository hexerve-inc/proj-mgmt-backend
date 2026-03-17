from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from api.deps import get_db, get_current_user
from schemas.user import UserResponse
from models.user import User

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(get_current_user)
):
    return current_user

