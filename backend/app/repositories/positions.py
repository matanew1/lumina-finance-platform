from collections.abc import Iterable

from sqlalchemy import delete, select

from backend.app.models.position import Position
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.positions import PositionSchema


class PositionRepository(BaseRepository):
    '''
    Repository for managing position data in the database.
    '''
    def list_client_positions(self, client_id: str) -> list[Position]:
        '''
        Retrieves the current positions for a given client.
        - Parameters:
            - client_id: str - The ID of the client whose positions are to be retrieved.
        - Returns:
            - list[Position]: A list of Position objects representing the client's current positions.
        '''
        statement = (
            select(Position)
            .where(Position.client_id == client_id)
            .order_by(Position.isin.asc())
        )
        return list(self.db.scalars(statement).all())

    def update_clients_positions(
        self,
        client_ids: Iterable[str],
        positions: list[PositionSchema],
    ) -> None:
        """
        Deletes all existing positions for the given client IDs and inserts the new positions.
        - Parameters:
            - client_ids: Iterable[str] - The IDs of the clients whose positions are to be updated.
            - positions: list[PositionSchema] - The list of new Position objects to be inserted.
        """
        client_id_list = list(client_ids)
        if not client_id_list:
            return

        self.db.execute(delete(Position).where(Position.client_id.in_(client_id_list)))

        position_rows = [
            Position(
                client_id=position.client_id,
                isin=position.isin,
                quantity=position.quantity,
                average_price=position.average_cost,
                market_price=position.market_price,
                realized_pnl=position.realized_pnl,
                unrealized_pnl=position.unrealized_pnl,
            )
            for position in positions
            if position.quantity > 0
        ]

        if position_rows:
            self.db.add_all(position_rows)

        self.db.flush()
