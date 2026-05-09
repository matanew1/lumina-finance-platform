from sqlalchemy import select

from backend.db.repositories.base import BaseRepository
from backend.db.models.transactions.model import Transaction


class ClientRepository(BaseRepository):
    def list_client_ids(self) -> list[str]:
        statement = select(Transaction.client_id).distinct().order_by(Transaction.client_id)
        return list(self.db.scalars(statement).all())
