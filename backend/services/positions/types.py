from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol, TypeAlias


class TransactionView(Protocol):
    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime


ClientPositionsResponse: TypeAlias = dict[str, Any]
PositionKey: TypeAlias = tuple[str, str]
PositionResponse: TypeAlias = dict[str, Any]
PositionResult: TypeAlias = dict[str, Any]


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

        total_cost = sum(
            (lot.quantity * lot.unit_cost for lot in self.open_lots),
            Decimal("0"),
        )
        return total_cost / self.quantity

    @property
    def unrealized_pnl(self) -> Decimal:
        return self.quantity * (self.market_price - self.average_cost)

    def as_dict(self) -> PositionResult:
        return {
            "client_id": self.client_id,
            "isin": self.isin,
            "quantity": self.quantity,
            "average_cost": self.average_cost,
            "market_price": self.market_price,
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
        }
