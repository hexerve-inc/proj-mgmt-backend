from sqlalchemy.orm import Session
from models.user import User
from schemas.user import UserCreate
from core.security import get_password_hash, verify_password, create_access_token
from typing import Optional
import uuid


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email, User.deleted_at.is_(None)).first()

    def register_user(self, user_in: UserCreate) -> User:
        hashed_password = get_password_hash(user_in.password)
        user = User(
            name=user_in.name,
            email=user_in.email,
            hashed_password=hashed_password,
        )
        self.db.add(user)
        self.db.flush()  # Flush to get user.id before assigning role

        # Assign default or requested RBAC role
        self._assign_default_role(user, requested_role_id=user_in.system_role_id)

        self.db.commit()
        self.db.refresh(user)
        return user

    def _assign_default_role(self, user: User, requested_role_id: Optional[str] = None) -> None:
        """Assign the default RBAC role to a newly registered user, or a specific role if requested.
        
        Falls back gracefully if the RBAC tables haven't been seeded yet,
        ensuring backward compatibility during the migration period.
        """
        try:
            from models.role import Role
            from models.user_role import UserRole

            role = None
            if requested_role_id:
                role = self.db.query(Role).filter(Role.id == requested_role_id, Role.deleted_at.is_(None)).first()
            
            if not role:
                target_slug = "developer"
                role = (
                    self.db.query(Role)
                    .filter(Role.slug == target_slug, Role.deleted_at.is_(None))
                    .first()
                )
                
            if not role:
                return  # RBAC not seeded yet — skip gracefully

            # Set system_role_id for quick lookups
            user.system_role_id = role.id

            # Create user_role assignment
            assignment = UserRole(
                id=str(uuid.uuid4()),
                user_id=user.id,
                role_id=role.id,
                scope_type="global",
            )
            self.db.add(assignment)
        except Exception:
            # If RBAC tables don't exist yet, skip silently
            pass

    def delete_user(self, user_id: str) -> bool:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        import datetime
        suffix = f"-del-{int(datetime.datetime.now().timestamp())}"
        user.email = f"{user.email}{suffix}"
        user.soft_delete()
        self.db.commit()
        return True

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

