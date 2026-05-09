from collections.abc import Iterable
from typing import Any

from sqlalchemy import delete, select

from backend.db.repositories.base import BaseRepository
from backend.db.models.positions.model import Position


class PositionRepository(BaseRepository):
    def list_client_positions(self, client_id: str) -> list[Position]:
        statement = select(Position).where(Position.client_id == client_id).order_by(Position.isin.asc())
        return list(self.db.scalars(statement).all())

    def update_clients_positions(self, client_ids: Iterable[str], positions: list[dict[str, Any]]) -> None:
        client_id_list = list(client_ids)
        if not client_id_list:
            return

        self.db.execute(delete(Position).where(Position.client_id.in_(client_id_list)))

        position_rows = [
            Position(
                client_id=position["client_id"],
                isin=position["isin"],
                quantity=position["quantity"],
                average_price=position["average_cost"],
                market_price=position["market_price"],
                realized_pnl=position["realized_pnl"],
                unrealized_pnl=position["unrealized_pnl"],
            )
            for position in positions
            if position["quantity"] > 0
        ]

        if position_rows:
            self.db.add_all(position_rows)

        self.db.flush()
