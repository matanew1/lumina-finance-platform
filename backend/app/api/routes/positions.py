from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.repositories.positions import PositionRepository
from backend.app.api.schemas.positions import ClientPositionsResponse
from backend.app.services.positions.positions_service import (
    get_client_positions as get_positions_use_case,
)

router = APIRouter(tags=["positions"])


@router.get(
    "/clients/{client_id}/positions",
    response_model=ClientPositionsResponse,
    status_code=status.HTTP_200_OK,
)
def get_client_positions(
    client_id: str,
    db: Session = Depends(get_db),
) -> ClientPositionsResponse:
    return get_positions_use_case(
        client_id=client_id,
        repository=PositionRepository(db),
    )
