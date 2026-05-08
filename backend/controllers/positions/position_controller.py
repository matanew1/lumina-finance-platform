from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.schemas.position_schema import ClientPositionsResponse
from backend.services.positions.position_service import PositionService
from backend.utils.exceptions import BadRequestError, NotFoundError

router = APIRouter(tags=["positions"])


class PositionController:
    def __init__(self, db: Session) -> None:
        self.service = PositionService(db=db)

    def get_client_positions(self, client_id: str):
        try:
            return self.service.get_client_positions(client_id=client_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
        except BadRequestError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


def get_position_controller(db: Session = Depends(get_db)) -> PositionController:
    return PositionController(db=db)


@router.get(
    "/clients/{client_id}/positions",
    response_model=ClientPositionsResponse,
    status_code=status.HTTP_200_OK,
)
def get_client_positions(
    client_id: str,
    controller: PositionController = Depends(get_position_controller),
):
    return controller.get_client_positions(client_id)
