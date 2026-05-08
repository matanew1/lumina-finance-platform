from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.db.models.transaction import Transaction
from backend.db.repositories.base_repository import BaseRepository
from backend.utils.db_errors import is_unique_constraint_error
from backend.utils.exceptions import ConflictError, PersistenceError


class TransactionRepository(BaseRepository):
    def bulk_create(self, records: list[dict[str, Any]]) -> None:
        transactions = [Transaction(**record) for record in records]

        try:
            self.db.add_all(transactions)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            if self._is_duplicate_transaction_id_error(exc):
                raise ConflictError("One or more transactions have duplicate transaction IDs.") from exc
            raise PersistenceError("Failed to persist uploaded transactions.") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise PersistenceError("Failed to persist uploaded transactions.") from exc

    @staticmethod
    def _is_duplicate_transaction_id_error(exc: IntegrityError) -> bool:
        return is_unique_constraint_error(
            exc,
            field_markers=(
                "transaction_id",
                "transactions.transaction_id",
                "ix_transactions_transaction_id",
            ),
        )
