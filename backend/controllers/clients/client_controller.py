from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.client_schema import ClientRead
from backend.services.clients.client_service import ClientService

router = APIRouter(tags=["clients"])


class ClientController:
    def __init__(self, db: Session) -> None:
        self.service = ClientService(db=db)

    def get_clients(self):
        return self.service.get_clients()


def get_client_controller(db: Session = Depends(get_db)) -> ClientController:
    return ClientController(db=db)


@router.get("/clients", response_model=list[ClientRead], status_code=status.HTTP_200_OK)
def get_clients(controller: ClientController = Depends(get_client_controller)):
    return controller.get_clients()
