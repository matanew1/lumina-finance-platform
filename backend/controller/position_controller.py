from sqlalchemy.orm import Session

from backend.services.position_service import PositionService
from backend.utils.responses import todo_response


class PositionController:
    def __init__(self, db: Session) -> None:
        self.service = PositionService(db=db)

    def get_client_positions(self, client_id: str):
        # TODO: add authorization and response mapping for client positions.
        try:
            return self.service.get_client_positions(client_id=client_id)
        except NotImplementedError as exc:
            return todo_response(str(exc), endpoint="GET /clients/{client_id}/positions")
