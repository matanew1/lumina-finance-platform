from decimal import Decimal

from backend.app.api.schemas.positions import ClientPositionsResponse, PositionRead
from backend.app.services.positions.schemas import PositionRepository


def get_client_positions(
    client_id: str,
    repository: PositionRepository,
) -> ClientPositionsResponse:
    positions = [
        PositionRead(
            client_id=position.client_id,
            isin=position.isin,
            quantity=position.quantity,
            average_cost=position.average_price,
            market_price=position.market_price,
            realized_pnl=position.realized_pnl,
            unrealized_pnl=position.unrealized_pnl,
        )
        for position in repository.list_client_positions(client_id)
    ]

    return ClientPositionsResponse(
        client_id=client_id,
        positions=positions,
        total_realized_pnl=sum(
            (position.realized_pnl for position in positions),
            Decimal("0"),
        ),
        total_unrealized_pnl=sum(
            (position.unrealized_pnl for position in positions),
            Decimal("0"),
        ),
    )
