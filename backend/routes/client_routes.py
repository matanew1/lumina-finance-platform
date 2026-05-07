from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.controller.client_controller import ClientController
from backend.db.session import get_db
from backend.schemas.common import TODO_RESPONSES

router = APIRouter(tags=["clients"])


def get_client_controller(db: Session = Depends(get_db)) -> ClientController:
    return ClientController(db=db)


@router.get("/clients", responses=TODO_RESPONSES)
def get_clients(controller: ClientController = Depends(get_client_controller)):
    # TODO: support pagination, sorting, and filters.
    return controller.get_clients()
