import uuid
from sqlalchemy import Column, String, ForeignKey, Table, Integer
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
    description = Column(String, nullable=True)
    capacity = Column(Integer, nullable=True, default=40)
    velocity = Column(Integer, nullable=True, default=0)
    
    project_manager_id = Column(String, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    lead_id = Column(String, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    product_manager_id = Column(String, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)

    project_manager = relationship("User", foreign_keys=[project_manager_id])
    lead = relationship("User", foreign_keys=[lead_id])
    product_manager = relationship("User", foreign_keys=[product_manager_id])
    
    members = relationship("User", secondary=team_members, backref="teams")
    projects = relationship("Project", back_populates="team")

    @property
    def project_ids(self):
        return [str(p.id) for p in self.projects]
