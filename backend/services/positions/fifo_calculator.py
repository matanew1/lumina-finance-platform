from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Iterable, Protocol

'''
Unrealized: What you could make if you sold right now.
Realized: What you actually made from the sale you already finished.
'''


class TransactionLike(Protocol):
    transaction_id: str
    client_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime


@dataclass
class OpenLot:
    quantity: Decimal
    unit_cost: Decimal


@dataclass
class PositionState:
    client_id: str
    isin: str
    open_lots: deque[OpenLot] = field(default_factory=deque)
    realized_pnl: Decimal = Decimal("0")
    market_price: Decimal = Decimal("0")

    @property
    def quantity(self) -> Decimal:
        return sum((lot.quantity for lot in self.open_lots), Decimal("0"))

    @property
    def average_cost(self) -> Decimal:
        if self.quantity == 0:
            return Decimal("0")
        total_cost = sum((lot.quantity * lot.unit_cost for lot in self.open_lots), Decimal("0"))
        return total_cost / self.quantity

    @property
    def unrealized_pnl(self) -> Decimal:
        return self.quantity * (self.market_price - self.average_cost)

    def apply_buy(self, transaction: TransactionLike) -> None:
        self.open_lots.append(OpenLot(quantity=transaction.quantity, unit_cost=transaction.price))

    def apply_sell(self, transaction: TransactionLike) -> None:
        remaining = transaction.quantity
        while remaining > 0 and self.open_lots:
            oldest = self.open_lots[0] # oldest lot is at the front of the deque
            consumed = min(oldest.quantity, remaining) # quantity consumed from this lot for the sell transaction
            self.realized_pnl += consumed * (transaction.price - oldest.unit_cost) # PnL realized from consuming this lot
            oldest.quantity -= consumed # reduce the quantity in the oldest lot by the consumed amount
            remaining -= consumed # reduce the remaining quantity to sell by the consumed amount
            if oldest.quantity == 0: # if the oldest lot has been fully consumed, remove it from the deque
                self.open_lots.popleft()

        if remaining > 0:
            raise ValueError(
                f"Sell transaction {transaction.transaction_id} exceeds available position for {transaction.isin}."
            )

    def as_dict(self) -> dict:
        return {
            "client_id": self.client_id,
            "isin": self.isin,
            "quantity": self.quantity,
            "average_cost": self.average_cost,
            "market_price": self.market_price,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
        }


def calculate_fifo_positions(transactions: Iterable[TransactionLike]) -> list[dict]:
    positions: dict[tuple[str, str], PositionState] = {}

    # Same-timestamp ties broken by DB id then transaction_id so FIFO ordering is deterministic.
    chronological_transactions = sorted(
        transactions,
        key=lambda transaction: (
            transaction.timestamp,
            getattr(transaction, "id", 0),
            transaction.transaction_id,
        ),
    )

    for transaction in chronological_transactions:
        key = (transaction.client_id, transaction.isin)
        state = positions.setdefault(
            key,
            PositionState(client_id=transaction.client_id, isin=transaction.isin),
        )
        state.market_price = transaction.price

        if transaction.action == "buy":
            state.apply_buy(transaction)
        elif transaction.action == "sell":
            state.apply_sell(transaction)
        else:
            raise ValueError(f"Unsupported transaction action: {transaction.action}.")

    return [state.as_dict() for state in positions.values()]
