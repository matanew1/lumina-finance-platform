from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.repositories.positions import PositionRepository
from backend.app.schemas.positions import ClientPositionsResponse
from backend.app.services.positions.positions_service import list_positions_by_client

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
    '''
    Returns the current positions for a given client.
    - Parameters:
        - client_id: str - The ID of the client whose positions are to be retrieved.
        - db: Session - The database session, injected by FastAPI's dependency injection system.
    - Returns:
        - ClientPositionsResponse: An object containing the client_id and a list of their current positions
    '''
    return list_positions_by_client(
        client_id=client_id,
        repository=PositionRepository(db),
    )
