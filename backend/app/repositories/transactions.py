from collections.abc import Iterable

from sqlalchemy import select

from backend.app.models.transaction import Transaction
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.transactions import TransactionIngested


class TransactionRepository(BaseRepository):
    """Repository for managing transaction data in the database."""

    def list_for_clients_ordered(self, client_ids: Iterable[str]) -> list[Transaction]:
        """Return all transactions for the given clients, ordered by (timestamp, id)."""
        client_id_list = list(client_ids)
        if not client_id_list:
            return []

        statement = (
            select(Transaction)
            .where(Transaction.client_id.in_(client_id_list))
            .order_by(Transaction.timestamp.asc(), Transaction.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def find_existing_transaction_ids(
        self,
        transaction_ids: Iterable[str],
    ) -> set[str]:
        """Return the subset of `transaction_ids` already persisted."""
        ids = list(transaction_ids)
        if not ids:
            return set()

        statement = select(Transaction.transaction_id).where(
            Transaction.transaction_id.in_(ids)
        )
        return set(self.db.scalars(statement).all())

    def add_records(self, records: Iterable[TransactionIngested]) -> None:
        """Persist new transaction records."""
        transactions = [Transaction(**record.model_dump()) for record in records]
        self.db.add_all(transactions)
        self.db.flush()
