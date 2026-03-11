from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from models.invoice import InvoiceStatus

class InvoiceBase(BaseModel):
    amount: float
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: datetime

class InvoiceCreate(InvoiceBase):
    client_id: str
    project_id: Optional[str] = None

class InvoiceUpdate(BaseModel):
    amount: Optional[float] = None
    status: Optional[InvoiceStatus] = None
    due_date: Optional[datetime] = None
    client_id: Optional[str] = None
    project_id: Optional[str] = None

class InvoiceResponse(InvoiceBase):
    id: str
    created_at: datetime
    client_id: str
    project_id: Optional[str]

    class Config:
        from_attributes = True
