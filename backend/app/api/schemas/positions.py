from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# Position Schemas
class PositionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    client_id: str
    isin: str
    quantity: Decimal
    average_cost: Decimal
    market_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


# Main Positions Response Model
class ClientPositionsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    client_id: str
    positions: list[PositionRead]
    total_realized_pnl: Decimal
    total_unrealized_pnl: Decimal
