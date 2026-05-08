from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.common import TODO_RESPONSES
from backend.services.client_service import ClientService
from backend.utils.responses import todo_response

router = APIRouter(tags=["clients"])


class ClientController:
    def __init__(self, db: Session) -> None:
        self.service = ClientService(db=db)

    def get_clients(self):
        # TODO: add request parameters and response mapping.
        try:
            return self.service.get_clients()
        except NotImplementedError as exc:
            return todo_response(str(exc), endpoint="GET /clients")


def get_client_controller(db: Session = Depends(get_db)) -> ClientController:
    return ClientController(db=db)


@router.get("/clients", responses=TODO_RESPONSES)
def get_clients(controller: ClientController = Depends(get_client_controller)):
    # TODO: support pagination, sorting, and filters.
    return controller.get_clients()
