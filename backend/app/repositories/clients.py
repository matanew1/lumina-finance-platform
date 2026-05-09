from sqlalchemy import select

from backend.app.models.transaction import Transaction
from backend.app.repositories.base import BaseRepository


class ClientRepository(BaseRepository):
    def list_client_ids(self) -> list[str]:
        statement = select(Transaction.client_id).distinct().order_by(Transaction.client_id)
        return list(self.db.scalars(statement).all())
