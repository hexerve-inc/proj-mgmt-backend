import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from core.database import Base

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    programs = relationship("Program", back_populates="portfolio")
