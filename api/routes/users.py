from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from api.deps import get_db, get_current_user, require_permission
from schemas.user import UserCreate, UserResponse, UserUpdate
from models.user import User
from models.role import Role
from services.auth_service import AuthService
from core.security import SUPER_ADMIN_EMAIL

router = APIRouter()

@router.get("/", response_model=List[UserResponse], dependencies=[Depends(require_permission("users:read"))])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    users = db.query(User).filter(User.deleted_at.is_(None)).offset(skip).limit(limit).all()
    return users

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_permission("users:create"))])
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new user (admin action). Requires authentication."""
    auth_service = AuthService(db)
    existing = auth_service.get_user_by_email(user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )
        
    if user_in.system_role_id:
        role = db.query(Role).filter(Role.id == user_in.system_role_id).first()
        if role and role.slug == "super_admin" and user_in.email != SUPER_ADMIN_EMAIL:
            raise HTTPException(status_code=403, detail="Cannot assign super admin role to this email.")

    new_user = auth_service.register_user(user_in)
    return new_user

@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_permission("users:read"))])
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_permission("users:update"))])
def update_user(
    user_id: str,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id, User.deleted_at.is_(None)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.email == SUPER_ADMIN_EMAIL:
        if user_in.email is not None and user_in.email != SUPER_ADMIN_EMAIL:
            raise HTTPException(status_code=403, detail="Cannot change the email of the super admin.")
        if user_in.system_role_id is not None and user_in.system_role_id != user.system_role_id:
            raise HTTPException(status_code=403, detail="Cannot change the role of the super admin.")
    
    if user_in.name is not None:
        user.name = user_in.name
    if user_in.email is not None:
        if user_in.email != user.email:
            existing = db.query(User).filter(User.email == user_in.email, User.deleted_at.is_(None)).first()
            if existing:
                raise HTTPException(status_code=400, detail="A user with this email already exists")
        user.email = user_in.email
    if user_in.system_role_id is not None:
        role = db.query(Role).filter(Role.id == user_in.system_role_id).first()
        if role and role.slug == "super_admin" and user.email != SUPER_ADMIN_EMAIL:
            raise HTTPException(status_code=403, detail="Cannot assign super admin role to this email.")
        user.system_role_id = user_in.system_role_id

    db.commit()
    db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission("users:delete"))])
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if str(user_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="Users cannot delete themselves")
        
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if user_to_delete and user_to_delete.email == SUPER_ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="The system super administrator cannot be deleted.")
        
    auth_service = AuthService(db)
    success = auth_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
