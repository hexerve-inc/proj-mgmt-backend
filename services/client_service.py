from sqlalchemy.orm import Session
from models.client import Client
from schemas.client import ClientCreate, ClientUpdate
from typing import Optional

class ClientService:
    def __init__(self, db: Session):
        self.db = db

    def create_client(self, client_in: ClientCreate) -> Client:
        client = Client(**client_in.model_dump())
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def get_clients(self) -> list[Client]:
        return self.db.query(Client).all()

    def get_client(self, client_id: str) -> Optional[Client]:
        return self.db.query(Client).filter(Client.id == client_id).first()

    def update_client(self, client_id: str, client_in: ClientUpdate) -> Optional[Client]:
        client = self.get_client(client_id)
        if not client:
            return None
            
        update_data = client_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)
            
        self.db.commit()
        self.db.refresh(client)
        return client

    def delete_client(self, client_id: str) -> bool:
        client = self.get_client(client_id)
        if not client:
            return False
            
        self.db.delete(client)
        self.db.commit()
        return True
