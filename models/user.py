import uuid
from sqlalchemy import Column, String, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin
import enum

class User(SoftDeleteMixin, Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)

    # New RBAC: default system-level role (quick lookup without joining user_roles)
    system_role_id = Column(
        String,
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────
    custom_filters = relationship("CustomFilter", back_populates="user", cascade="all, delete-orphan")
    system_role = relationship("Role", foreign_keys=[system_role_id])
    user_roles = relationship(
        "UserRole",
        back_populates="user",
        foreign_keys="UserRole.user_id",
        cascade="all, delete-orphan",
    )

    @property
    def role(self):
        """Expose the system role name for the frontend."""
        return self.system_role.name if self.system_role else None
