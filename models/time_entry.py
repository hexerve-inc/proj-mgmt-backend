import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    duration = Column(Integer, nullable=False) # Duration in minutes
    date = Column(DateTime, default=func.now(), nullable=False)
    description = Column(String, nullable=True)
    
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    task = relationship("Task", backref="time_entries")
    
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", backref="time_entries")
