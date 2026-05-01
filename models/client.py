import uuid
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from core.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    type = Column(String, nullable=True, default="external") # external, internal
    address = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    
    projects = relationship("Project", back_populates="client")
    invoices = relationship("Invoice", back_populates="client")
