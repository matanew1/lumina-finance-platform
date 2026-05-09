from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.db.repositories.base import BaseRepository
from backend.db.models.transactions.model import Transaction
from backend.utils.errors.exceptions import (
    ConflictError,
    PersistenceError,
    is_unique_constraint_error,
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

    def add_records(self, records: list[dict[str, Any]]) -> list[Transaction]:
        transactions = [Transaction(**record) for record in records]
        self.db.add_all(transactions)
        self.db.flush()
        return transactions

    def bulk_create(self, records: list[dict[str, Any]]) -> None:
        try:
            self.add_records(records)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if self.is_duplicate_transaction_id_error(exc):
                raise ConflictError("One or more transactions have duplicate transaction IDs.") from exc
            raise PersistenceError("Failed to persist uploaded transactions.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise PersistenceError("Failed to persist uploaded transactions.") from exc

    @staticmethod
    def is_duplicate_transaction_id_error(exc: IntegrityError) -> bool:
        return is_unique_constraint_error(
            exc,
            field_markers=(
                "transaction_id",
                "transactions.transaction_id",
                "ix_transactions_transaction_id",
            ),
        )
