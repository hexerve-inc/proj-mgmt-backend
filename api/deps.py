from collections.abc import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from core.database import SessionLocal
from core.security import ALGORITHM, SECRET_KEY
from services.auth_service import AuthService
from services.permission_service import PermissionService
from models.user import User
from schemas.user import TokenData
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    auth_service = AuthService(db)
    user = auth_service.get_user_by_email(email=token_data.email)
    if user is None:
        raise credentials_exception

    if user.password_changed_at:
        iat = payload.get("iat")
        if iat:
            from datetime import datetime, timezone
            if datetime.fromtimestamp(iat, tz=timezone.utc) < user.password_changed_at:
                raise credentials_exception

    return user


# ── RBAC Dependencies ────────────────────────────────────────────

def get_permission_service(db: Session = Depends(get_db)) -> PermissionService:
    """Inject the centralized permission service."""
    return PermissionService(db)


def require_permission(
    *permissions: str,
    scope_type: Optional[str] = None,
):
    """FastAPI dependency factory that enforces permission checks.

    Usage (declarative — route-level guard):
        @router.post("/", dependencies=[Depends(require_permission("projects:create"))])
        def create_project(...):
            ...

    Usage (injected — for scope checks within the handler):
        def update_task(
            checker = Depends(require_permission("tasks:update")),
        ):
            checker.check_scope("project", task.project_id)

    Multiple permissions mean ALL are required (AND logic).
    For OR logic, use ``require_any_permission()``.
    """

    class PermissionChecker:
        def __init__(
            self,
            current_user: User = Depends(get_current_user),
            perm_service: PermissionService = Depends(get_permission_service),
        ):
            self.user = current_user
            self.perm_service = perm_service
            # Check all required permissions immediately
            for perm in permissions:
                perm_service.check_permission(
                    user_id=current_user.id,
                    permission=perm,
                    scope_type=scope_type,
                )

        def check_scope(self, s_type: str, s_id: str) -> None:
            """Additional scope check within the route handler."""
            for perm in permissions:
                self.perm_service.check_permission(
                    user_id=self.user.id,
                    permission=perm,
                    scope_type=s_type,
                    scope_id=s_id,
                )

    return PermissionChecker


def require_any_permission(*permissions: str):
    """FastAPI dependency factory — at least ONE permission is required (OR logic).

    Usage:
        @router.get("/", dependencies=[require_any_permission("tasks:read", "tasks:read_own")])
    """

    def checker(
        current_user: User = Depends(get_current_user),
        perm_service: PermissionService = Depends(get_permission_service),
    ):
        for perm in permissions:
            if perm_service.has_permission(current_user.id, perm):
                return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required one of: {', '.join(permissions)}",
        )

    return checker

