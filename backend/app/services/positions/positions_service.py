from decimal import Decimal

from backend.app.schemas.positions import ClientPositionsResponse
from backend.app.models.position import Position
from backend.app.repositories.positions import PositionRepository


def list_positions_by_client(
    client_id: str,
    repository: PositionRepository,
) -> ClientPositionsResponse:
    '''
    Retrieves the current positions for a given client.
    - Parameters:
        - client_id: str - The ID of the client whose positions are to be retrieved.
        - repository: PositionRepository - An instance of PositionRepository to access position data.
    - Returns:
        - ClientPositionsResponse: An object containing the client_id and a list of their current positions
    '''

    # Retrieve the client's positions from the repository
    positions: list[Position] = repository.list_client_positions(client_id)

    # Calculate the total realized and unrealized P&L for the client
    return ClientPositionsResponse(
        client_id=client_id, # The ID of the client for whom the positions are being retrieved
        positions=positions, # The list of Position objects representing the client's current positions
        
        # Calculate the total realized P&L by summing the realized_pnl of each position, starting with a Decimal value of 0
        total_realized_pnl=sum(
            (position.realized_pnl for position in positions),
            Decimal("0"),
        ),

        # Calculate the total unrealized P&L by summing the unrealized_pnl of each position, starting with a Decimal value of 0
        total_unrealized_pnl=sum(
            (position.unrealized_pnl for position in positions),
            Decimal("0"),
        ),
    )

