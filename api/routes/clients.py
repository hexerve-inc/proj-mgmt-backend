from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from api.deps import get_db
from schemas.client import ClientCreate, ClientResponse, ClientUpdate
from services.client_service import ClientService

router = APIRouter()

@router.post("/", response_model=ClientResponse)
def create_client(client_in: ClientCreate, db: Session = Depends(get_db)):
    service = ClientService(db)
    return service.create_client(client_in)

@router.get("/", response_model=list[ClientResponse])
def get_clients(db: Session = Depends(get_db)):
    service = ClientService(db)
    return service.get_clients()

@router.get("/{client_id}", response_model=ClientResponse)
def get_client(client_id: str, db: Session = Depends(get_db)):
    service = ClientService(db)
    client = service.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client
