from sqlalchemy import select

from backend.app.models.position import Position
from backend.app.models.transaction import Transaction
from backend.app.repositories.base import BaseRepository


class AnalyticsRepository(BaseRepository):
    def list_transactions_ordered(self) -> list[Transaction]:
        statement = select(Transaction).order_by(
            Transaction.timestamp.asc(),
            Transaction.id.asc(),
            Transaction.transaction_id.asc(),
        )
        return list(self.db.scalars(statement).all())

    def list_current_positions(self) -> list[Position]:
        statement = (
            select(Position)
            .where(Position.quantity > 0)
            .order_by(Position.isin.asc(), Position.client_id.asc())
        )
        return list(self.db.scalars(statement).all())
