from collections.abc import Iterable

from backend.services.positions.types import (
    OpenLot,
    PositionKey,
    PositionResult,
    PositionState,
    TransactionView,
)

'''
Description:
Realized P&L = (Sell Price - Buy Price) * Quantity Sold
Unrealized P&L = (Current Market Price - Average Cost) * Quantity Held

FIFO Logic:
1. When a buy transaction occurs, we add the quantity and price to a queue (representing the lots).
2. When a sell transaction occurs, we consume from the queue starting with the oldest lot until the sell quantity is fulfilled. 
3. For each consumed lot, we calculate the realized P&L based on the difference between the sell price and the buy price of that lot.
4. After processing all transactions, we calculate the average cost and unrealized P&L for the remaining quantity in the queue.
'''

TIMESTAMP_SORT_FUNC = lambda item: (item.timestamp, getattr(item, "id", 0), item.transaction_id)


class FifoCalculator:
    def calculate(self, transactions: Iterable[TransactionView]) -> list[PositionResult]:
        positions: dict[PositionKey, PositionState] = {}

        for transaction in sorted(transactions, key=TIMESTAMP_SORT_FUNC):
            position = self._position_for_transaction(positions, transaction)
            position.market_price = transaction.price

            if transaction.action == "buy":
                position.open_lots.append(
                    OpenLot(quantity=transaction.quantity, unit_cost=transaction.price)
                )
            elif transaction.action == "sell":
                self._apply_sell(transaction, position)
            else:
                raise ValueError(f"Unsupported transaction action: {transaction.action}.")

        return [position.as_dict() for position in positions.values()]

    def _position_for_transaction(
        self,
        positions: dict[PositionKey, PositionState],
        transaction: TransactionView,
    ) -> PositionState:
        key = (transaction.client_id, transaction.isin)
        return positions.setdefault(
            key,
            PositionState(client_id=transaction.client_id, isin=transaction.isin),
        )

    def _apply_sell(self, transaction: TransactionView, position: PositionState) -> None:
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
            raise ValueError(
                f"Sell transaction {transaction.transaction_id} exceeds available position for {transaction.isin}."
            )


calculate_fifo_positions = FifoCalculator().calculate
