from decimal import Decimal

from pydantic import Field

from backend.schemas.common import OrmSchema


class PositionRead(OrmSchema):
    client_id: str = Field(examples=["C001"])
    isin: str = Field(examples=["US1234567890"])
    quantity: Decimal = Field(examples=["30"])
    average_cost: Decimal = Field(examples=["100.5"])
    market_price: Decimal = Field(examples=["105.2"])
    realized_pnl: Decimal = Field(examples=["94"])
    unrealized_pnl: Decimal = Field(examples=["141"])


class ClientPositionsResponse(OrmSchema):
    client_id: str = Field(examples=["C001"])
    positions: list[PositionRead]
    total_realized_pnl: Decimal = Field(examples=["94"])
    total_unrealized_pnl: Decimal = Field(examples=["141"])
