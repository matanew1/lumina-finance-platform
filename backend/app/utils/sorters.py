from typing import Any

from backend.app.schemas.shared import TransactionView


def sort_by_timestamp(transaction: TransactionView) -> Any:
    return transaction.timestamp


def sort_by_timestamp_and_id(transaction: TransactionView) -> tuple[Any, int]:
    return (transaction.timestamp, getattr(transaction, "id", 0))


def sort_by_timestamp_id_and_transaction_id(
    transaction: TransactionView,
) -> tuple[Any, int, str]:
    return (
        transaction.timestamp,
        getattr(transaction, "id", 0),
        transaction.transaction_id,
    )
