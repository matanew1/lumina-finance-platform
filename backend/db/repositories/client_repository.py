from sqlalchemy import select

from backend.db.models.transaction import Transaction
from backend.db.repositories.base_repository import BaseRepository


class ClientRepository(BaseRepository):
    def list_client_ids(self) -> list[str]:
        statement = select(Transaction.client_id).distinct().order_by(Transaction.client_id)
        return list(self.db.scalars(statement).all())
