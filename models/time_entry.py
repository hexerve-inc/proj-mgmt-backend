import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base

class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    duration = Column(Integer, nullable=True) # Duration in minutes, computed on stop
    date = Column(DateTime, default=func.now(), nullable=False)
    description = Column(String, nullable=True)
    
    # Timer-based activity tracking fields
    start_at = Column(DateTime(timezone=True), nullable=True)  # When the timer started (UTC)
    end_at = Column(DateTime(timezone=True), nullable=True)    # When the timer stopped (UTC)
    is_running = Column(Boolean, default=False, nullable=False) # Whether this entry is currently active
    
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    task = relationship("Task", backref="time_entries")
    
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", backref="time_entries")
