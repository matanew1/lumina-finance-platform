from decimal import Decimal

from backend.db.repositories.positions.repository import PositionRepository
from backend.services.positions.fifo_calculator import FifoCalculator
from backend.services.positions.types import (
    ClientPositionsResponse,
    PositionResponse,
    PositionResult,
    TransactionView,
)


class PositionService:
    def __init__(
        self,
        position_repository: PositionRepository,
        fifo_calculator: FifoCalculator | None = None,
    ) -> None:
        self.position_repository = position_repository
        self.fifo_calculator = fifo_calculator or FifoCalculator()

    def get_client_positions(self, client_id: str) -> ClientPositionsResponse:
        positions: list[PositionResponse] = [
            {
                "client_id": position.client_id,
                "isin": position.isin,
                "quantity": position.quantity,
                "average_cost": position.average_price,
                "market_price": position.market_price,
                "realized_pnl": position.realized_pnl,
                "unrealized_pnl": position.unrealized_pnl,
            }
            for position in self.position_repository.list_client_positions(client_id)
        ]

        return {
            "client_id": client_id,
            "positions": positions,
            "total_realized_pnl": sum((position["realized_pnl"] for position in positions), Decimal("0")),
            "total_unrealized_pnl": sum((position["unrealized_pnl"] for position in positions), Decimal("0")),
        }

    def update_clients_positions(
        self,
        client_ids: list[str],
        transactions: list[TransactionView],
    ) -> list[PositionResult]:
        positions = self.fifo_calculator.calculate(transactions)
        self.position_repository.update_clients_positions(client_ids, positions)
        return positions
