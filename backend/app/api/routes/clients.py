from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.repositories.clients import ClientRepository
from backend.app.api.schemas.clients import ClientResponse
from backend.app.services.clients.clients_service import list_clients

router = APIRouter(tags=["clients"])


@router.get(
    "/clients",
    response_model=list[ClientResponse],
    status_code=status.HTTP_200_OK,
)
def get_clients(db: Session = Depends(get_db)) -> list[ClientResponse]:
    return list_clients(ClientRepository(db))
