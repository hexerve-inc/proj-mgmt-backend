import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from core.database import Base

class Program(Base):
    __tablename__ = "programs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    projects = relationship("Project", back_populates="program")
