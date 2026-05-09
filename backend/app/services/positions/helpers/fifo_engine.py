from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from backend.app.utils.exceptions import InsufficientQuantityError, ValidationAppError

from backend.app.schemas.positions import OpenLot, PositionSchema, PositionState
from backend.app.schemas.shared import TransactionView
from backend.app.utils.sorters import sort_by_timestamp_id_and_transaction_id


def calculate_fifo_positions(
    transactions: Iterable[TransactionView],
) -> list[PositionSchema]:
    """
    Calculates the positions of clients based on their transactions using the FIFO (First-In, First-Out) method.
    
    - Parameters:
        - transactions: Iterable[TransactionView] - The transactions to process.
    - Returns:
        - list[PositionSchema] - The calculated positions for the clients.
    """

    # dictionary to store the positions of each client
    positions: dict[tuple[str, str], PositionState] = {}

    # sort transactions by timestamp and then by transaction_id to ensure FIFO order
    for transaction in sorted(
        transactions,
        key=sort_by_timestamp_id_and_transaction_id,
    ):
        position = _position_for_transaction(positions, transaction)
        position.market_price = transaction.price

        if transaction.action == "buy":
            _apply_buy(transaction, position)
        elif transaction.action == "sell":
            _apply_sell(transaction, position)
        else:
            raise ValidationAppError(
                f"Unsupported transaction action: {transaction.action}."
            )

    return [position.as_result() for position in positions.values()]


def _position_for_transaction(
    positions: dict[tuple[str, str], PositionState],
    transaction: TransactionView,
) -> PositionState:
    key = (transaction.client_id, transaction.isin)
    return positions.setdefault(
        key,
        PositionState(client_id=transaction.client_id, isin=transaction.isin),
    )



def _apply_buy(transaction: TransactionView, position: PositionState) -> None:
    position.open_lots.append(
        OpenLot(quantity=transaction.quantity, unit_cost=transaction.price)
    )
    
def _apply_sell(transaction: TransactionView, position: PositionState) -> None:
    remaining = transaction.quantity
    lots = position.open_lots

    while remaining > 0 and lots:
        oldest_lot = lots[0]
        consumed = min(oldest_lot.quantity, remaining)
        position.realized_pnl += consumed * (transaction.price - oldest_lot.unit_cost)
        oldest_lot.quantity -= consumed
        remaining -= consumed

        if oldest_lot.quantity == 0:
            lots.popleft()

    if remaining > 0:
        raise InsufficientQuantityError(
            f"Sell transaction {transaction.transaction_id} exceeds available position "
            f"for {transaction.isin}."
        )
