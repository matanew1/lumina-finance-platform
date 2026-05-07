from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.controller.position_controller import PositionController
from backend.db.session import get_db
from backend.schemas.common import TODO_RESPONSES

router = APIRouter(tags=["positions"])


def get_position_controller(db: Session = Depends(get_db)) -> PositionController:
    return PositionController(db=db)


@router.get("/clients/{client_id}/positions", responses=TODO_RESPONSES)
def get_client_positions(
    client_id: str,
    controller: PositionController = Depends(get_position_controller),
):
    # TODO: validate client identifier and return calculated positions.
    return controller.get_client_positions(client_id)
