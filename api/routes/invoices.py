from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db, require_permission
from schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceUpdate
from services.invoice_service import InvoiceService

router = APIRouter()

@router.post("/", response_model=InvoiceResponse, dependencies=[Depends(require_permission("invoices:create"))])
def create_invoice(invoice_in: InvoiceCreate, db: Session = Depends(get_db)):
    service = InvoiceService(db)
    return service.create_invoice(invoice_in)

@router.get("/", response_model=list[InvoiceResponse], dependencies=[Depends(require_permission("invoices:read"))])
def get_invoices(db: Session = Depends(get_db)):
    service = InvoiceService(db)
    return service.get_invoices()

@router.get("/{invoice_id}", response_model=InvoiceResponse, dependencies=[Depends(require_permission("invoices:read"))])
def get_invoice(invoice_id: str, db: Session = Depends(get_db)):
    service = InvoiceService(db)
    invoice = service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice
