from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.repositories.clients import ClientRepository
from backend.app.schemas.clients import ClientResponse
from backend.app.services.clients.clients_service import list_clients

router = APIRouter(tags=["clients"])

@router.get(
    "/clients",
    response_model=list[ClientResponse],
    status_code=status.HTTP_200_OK,
)
def get_clients(db: Session = Depends(get_db)) -> list[ClientResponse]:
    '''
    Returns a list of all clients.
    - Parameters:
        - db: Session - The database session, injected by FastAPI's dependency injection system.
    - Returns:
        - list[ClientResponse]: A list of ClientResponse objects, each containing a client_id.
    '''
    return list_clients(ClientRepository(db))
