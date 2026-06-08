import uuid
from sqlalchemy import Column, String, Float, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base
from models.soft_delete_mixin import SoftDeleteMixin
import enum

class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"

class Invoice(SoftDeleteMixin, Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    amount = Column(Float, nullable=False)
    status = Column(Enum(InvoiceStatus, name="invoice_status_enum"), default=InvoiceStatus.DRAFT, nullable=False)
    due_date = Column(DateTime, nullable=False)
    # created_at, updated_at, deleted_at inherited from SoftDeleteMixin
    
    client_id = Column(String, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    client = relationship("Client", back_populates="invoices")
    
    project_id = Column(String, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    project = relationship("Project", back_populates="invoices")
