from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.app.models.transaction import Transaction
from backend.app.repositories.base import BaseRepository
from backend.app.services.transactions.schemas import TransactionIngested

UNIQUE_CONSTRAINT_MARKERS = (
    "duplicate key value violates unique constraint",
    "unique constraint failed",
    "duplicate entry",
)


class TransactionRepository(BaseRepository):
    def list_for_clients_ordered(self, client_ids: Iterable[str]) -> list[Transaction]:
        client_id_list = list(client_ids)
        if not client_id_list:
            return []

        statement = (
            select(Transaction)
            .where(Transaction.client_id.in_(client_id_list))
            .order_by(Transaction.timestamp.asc(), Transaction.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def add_records(self, records: Iterable[TransactionIngested]) -> list[Transaction]:
        transactions = [Transaction(**record.model_dump()) for record in records]
        self.db.add_all(transactions)
        self.db.flush()
        return transactions

    @staticmethod
    def is_duplicate_transaction_id_error(exc: IntegrityError) -> bool:
        message = str(exc).lower()
        if not any(marker in message for marker in UNIQUE_CONSTRAINT_MARKERS):
            return False

        return any(
            marker in message
            for marker in (
                "transaction_id",
                "transactions.transaction_id",
                "ix_transactions_transaction_id",
            )
        )
