from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel

from backend.app.utils.exceptions import InsufficientQuantityError, ValidationAppError


class TransactionView(Protocol):
    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime


class PositionCalculation(BaseModel):
    client_id: str
    isin: str
    quantity: Decimal
    average_cost: Decimal
    market_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


class OpenLot(BaseModel):
    quantity: Decimal
    unit_cost: Decimal


class PositionState:
    def __init__(self, *, client_id: str, isin: str) -> None:
        self.client_id = client_id
        self.isin = isin
        self.open_lots: deque[OpenLot] = deque()
        self.realized_pnl = Decimal("0")
        self.market_price = Decimal("0")

    @property
    def quantity(self) -> Decimal:
        return sum((lot.quantity for lot in self.open_lots), Decimal("0"))

    @property
    def average_cost(self) -> Decimal:
        if self.quantity == 0:
            return Decimal("0")

        total_cost = sum(
            (lot.quantity * lot.unit_cost for lot in self.open_lots),
            Decimal("0"),
        )
        return total_cost / self.quantity

    @property
    def unrealized_pnl(self) -> Decimal:
        return self.quantity * (self.market_price - self.average_cost)

    def as_result(self) -> PositionCalculation:
        return PositionCalculation(
            client_id=self.client_id,
            isin=self.isin,
            quantity=self.quantity,
            average_cost=self.average_cost,
            market_price=self.market_price,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
        )


def calculate_fifo_positions(
    transactions: Iterable[TransactionView],
) -> list[PositionCalculation]:
    positions: dict[tuple[str, str], PositionState] = {}

    for transaction in sorted(
        transactions,
        key=lambda item: (item.timestamp, getattr(item, "id", 0), item.transaction_id),
    ):
        position = _position_for_transaction(positions, transaction)
        position.market_price = transaction.price

        if transaction.action == "buy":
            position.open_lots.append(
                OpenLot(quantity=transaction.quantity, unit_cost=transaction.price)
            )
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
