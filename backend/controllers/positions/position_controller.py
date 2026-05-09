from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.database import get_db
from backend.db.repositories.positions.repository import PositionRepository
from backend.schemas.positions.schema import ClientPositionsResponse
from backend.services.positions.position_service import PositionService
from backend.utils.errors.exceptions import BadRequestError, NotFoundError

router = APIRouter(tags=["positions"])


def get_position_service(db: Session = Depends(get_db)) -> PositionService:
    return PositionService(position_repository=PositionRepository(db))


@router.get(
    "/clients/{client_id}/positions",
    response_model=ClientPositionsResponse,
    status_code=status.HTTP_200_OK,
)
def get_client_positions(
    client_id: str,
    service: PositionService = Depends(get_position_service),
):
    try:
        return service.get_client_positions(client_id=client_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except BadRequestError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
