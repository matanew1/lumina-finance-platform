from decimal import Decimal

from sqlalchemy.orm import Session

from backend.db.repositories.position_repository import PositionRepository


class PositionService:
    def __init__(
        self,
        db: Session,
        position_repository: PositionRepository | None = None,
    ) -> None:
        self.position_repository = position_repository or PositionRepository(db)

    def get_client_positions(self, client_id: str) -> dict:
        positions = [
            self._position_to_response(position)
            for position in self.position_repository.list_client_positions(client_id)
        ]

        return {
            "client_id": client_id,
            "positions": positions,
            "total_realized_pnl": sum((position["realized_pnl"] for position in positions), Decimal("0")),
            "total_unrealized_pnl": sum((position["unrealized_pnl"] for position in positions), Decimal("0")),
        }

    @staticmethod
    def _position_to_response(position) -> dict:
        return {
            "client_id": position.client_id,
            "isin": position.isin,
            "quantity": position.quantity,
            "average_cost": position.average_price,
            "market_price": position.market_price,
            "realized_pnl": position.realized_pnl,
            "unrealized_pnl": position.unrealized_pnl,
        }
