from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.repositories.clients.repository import ClientRepository
from backend.schemas.clients.schema import ClientResponse
from backend.services.clients.client_service import ClientService

router = APIRouter(tags=["clients"])


def get_client_service(db: Session = Depends(get_db)) -> ClientService:
    return ClientService(client_repository=ClientRepository(db))


@router.get("/clients", response_model=list[ClientResponse], status_code=status.HTTP_200_OK)
def get_clients(service: ClientService = Depends(get_client_service)):
    return service.get_clients()
