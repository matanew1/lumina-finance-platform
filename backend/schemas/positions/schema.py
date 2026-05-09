from dataclasses import dataclass
from decimal import Decimal

from pydantic import BaseModel


class PositionRead(BaseModel):
    client_id: str
    isin: str
    quantity: Decimal
    average_cost: Decimal
    market_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


class ClientPositionsResponse(BaseModel):
    client_id: str
    positions: list[PositionRead]
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal
