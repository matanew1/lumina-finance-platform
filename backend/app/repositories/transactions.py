from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.app.models.transaction import Transaction
from backend.app.repositories.base import BaseRepository
from backend.app.schemas.transactions import TransactionIngested

UNIQUE_CONSTRAINT_MARKERS = (
    "duplicate key value violates unique constraint",
    "unique constraint failed",
    "duplicate entry",
)


class TransactionRepository(BaseRepository):
    '''
    Repository for managing transaction data in the database.
    '''
    def list_for_clients_ordered(self, client_ids: Iterable[str]) -> list[Transaction]:
        '''
        Retrieves a list of transactions for the specified client IDs, ordered by timestamp and ID.
        - Parameters:
            - client_ids (Iterable[str]): An iterable of client IDs for which to retrieve transactions.
        - Returns:
            - list[Transaction]: A list of Transaction objects representing the retrieved transactions.
        '''
        client_id_list = list(client_ids)
        if not client_id_list:
            return []

        statement = (
            select(Transaction)
            .where(Transaction.client_id.in_(client_id_list))
            .order_by(Transaction.timestamp.asc(), Transaction.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def add_records(self, records: Iterable[TransactionIngested]) -> None:
        '''
        Adds new transaction records to the database.
        - Parameters:
            - records (Iterable[TransactionIngested]): An iterable of TransactionIngested objects representing the transactions to be added.
        '''
        transactions = [Transaction(**record.model_dump()) for record in records]
        self.db.add_all(transactions)
        self.db.flush()

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
