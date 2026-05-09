"""
Position-specific schemas.

Protocol types (TransactionView, PositionView) live in shared.protocols and are
re-exported here so callers importing from this module continue to work.
"""
from collections import deque
from decimal import ROUND_HALF_EVEN, Decimal

from pydantic import BaseModel

from backend.app.schemas.shared import PositionView, TransactionView
from backend.app.utils.constants import MONEY_QUANTUM, ZERO

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
        self.realized_pnl = ZERO
        self.market_price = ZERO
        # Running totals updated incrementally on each buy/sell. Avoids walking
        # all open lots on every property read and keeps unrealized_pnl free of
        # divide-then-multiply drift from the average_cost computation.
        self.total_quantity = ZERO
        self.total_cost_basis = ZERO

    @property
    def quantity(self) -> Decimal:
        return self.total_quantity

    @property
    def average_cost(self) -> Decimal:
        if self.total_quantity == 0:
            return ZERO
        return _quantize_money(self.total_cost_basis / self.total_quantity)

    @property
    def unrealized_pnl(self) -> Decimal:
        # Computed from running totals, not from average_cost, so the result
        # does not inherit rounding from the division above.
        return self.market_price * self.total_quantity - self.total_cost_basis

    def as_result(self) -> PositionSchema:
        return PositionSchema(
            client_id=self.client_id,
            isin=self.isin,
            quantity=self.total_quantity,
            average_cost=self.average_cost,
            market_price=self.market_price,
            realized_pnl=_quantize_money(self.realized_pnl),
            unrealized_pnl=_quantize_money(self.unrealized_pnl),
        )


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_EVEN)
