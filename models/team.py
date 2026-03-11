import uuid
from sqlalchemy import Column, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from core.database import Base

team_members = Table(
    'team_members', Base.metadata,
    Column('team_id', String, ForeignKey('teams.id', ondelete="CASCADE"), primary_key=True),
    Column('user_id', String, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True)
)

class Team(Base):
    __tablename__ = "teams"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    
    members = relationship("User", secondary=team_members, backref="teams")
    projects = relationship("Project", back_populates="team")
