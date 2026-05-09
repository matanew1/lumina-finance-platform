"""
Position-specific schemas.

Protocol types (TransactionView, PositionView) live in shared.protocols and are
re-exported here so callers importing from this module continue to work.
"""
from collections import deque
from decimal import Decimal

from pydantic import BaseModel

from backend.app.schemas.shared import PositionView, TransactionView

__all__ = [
    "PositionSnapshot",
    "PositionSchema",
    "PositionState",
    "ClientPositionsResponse",
    "PositionView",
    "TransactionView",
]


class PositionSnapshot(BaseModel):
    client_id: str
    isin: str
    quantity: Decimal
    market_price: Decimal
    transaction_id: str | None = None


class PositionSchema(BaseModel):
    '''
    Schema representing a client's position in a specific security (identified by ISIN).
    '''
    model_config = {"from_attributes": True}

    client_id: str
    isin: str
    quantity: Decimal
    average_cost: Decimal
    market_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


class ClientPositionsResponse(BaseModel):
    '''
    Schema representing the response for a client's positions request.
    '''
    model_config = {"from_attributes": True}

    client_id: str
    positions: list[PositionSchema]
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal


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

    def as_result(self) -> PositionSchema:
        return PositionSchema(
            client_id=self.client_id,
            isin=self.isin,
            quantity=self.quantity,
            average_cost=self.average_cost,
            market_price=self.market_price,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
        )
