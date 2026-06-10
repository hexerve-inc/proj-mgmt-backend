import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin

class Program(SoftDeleteMixin, Base):
    __tablename__ = "programs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    portfolio_id = Column(String, ForeignKey("portfolios.id", ondelete="SET NULL"), nullable=True)
    
    portfolio = relationship("Portfolio", back_populates="programs")
    projects = relationship("Project", back_populates="program")
