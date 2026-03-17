import uuid
from sqlalchemy import Column, String, ForeignKey, Date, Integer
from sqlalchemy.orm import relationship
from core.database import Base

class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    goal = Column(String, nullable=True)
    status = Column(String, default="active") # active, completed, future
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    velocity = Column(Integer, default=0)
    
    tasks = relationship("Task", back_populates="sprint")
