from sqlalchemy.orm import Session
from models.invoice import Invoice
from schemas.invoice import InvoiceCreate, InvoiceUpdate
from typing import Optional

class InvoiceService:
    def __init__(self, db: Session):
        self.db = db

    def create_invoice(self, invoice_in: InvoiceCreate) -> Invoice:
        invoice = Invoice(**invoice_in.model_dump())
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_invoices(self) -> list[Invoice]:
        return self.db.query(Invoice).filter(Invoice.deleted_at.is_(None)).all()

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        return self.db.query(Invoice).filter(Invoice.id == invoice_id, Invoice.deleted_at.is_(None)).first()

    def update_invoice(self, invoice_id: str, invoice_in: InvoiceUpdate) -> Optional[Invoice]:
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return None
            
        update_data = invoice_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invoice, field, value)
            
        self.db.commit()
        self.db.refresh(invoice)
        return invoice
