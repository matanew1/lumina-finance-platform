from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.common import TODO_RESPONSES
from backend.services.position_service import PositionService
from backend.utils.responses import todo_response

router = APIRouter(tags=["positions"])


class PositionController:
    def __init__(self, db: Session) -> None:
        self.service = PositionService(db=db)

    def get_client_positions(self, client_id: str):
        # TODO: add authorization and response mapping for client positions.
        try:
            return self.service.get_client_positions(client_id=client_id)
        except NotImplementedError as exc:
            return todo_response(str(exc), endpoint="GET /clients/{client_id}/positions")


def get_position_controller(db: Session = Depends(get_db)) -> PositionController:
    return PositionController(db=db)


@router.get("/clients/{client_id}/positions", responses=TODO_RESPONSES)
def get_client_positions(
    client_id: str,
    controller: PositionController = Depends(get_position_controller),
):
    # TODO: validate client identifier and return calculated positions.
    return controller.get_client_positions(client_id)
