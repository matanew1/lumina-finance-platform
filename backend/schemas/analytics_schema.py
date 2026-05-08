from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from backend.schemas.common import OrmSchema


class TopTradedIsin(BaseModel):
    isin: str = Field(examples=["US1234567890"])
    transaction_count: int = Field(examples=[12])


class ClientAverageHoldingTime(BaseModel):
    client_id: str = Field(examples=["C001"])
    average_holding_seconds: Decimal = Field(examples=["86400"])
    average_holding_days: Decimal = Field(examples=["1.00"])
    closed_quantity: Decimal = Field(examples=["15"])


class MostVolatileClient(BaseModel):
    client_id: str = Field(examples=["C001"])
    min_portfolio_value: Decimal = Field(examples=["1000"])
    max_portfolio_value: Decimal = Field(examples=["2500"])
    value_range: Decimal = Field(examples=["1500"])


class IsinConcentrationEntry(BaseModel):
    isin: str = Field(examples=["US1234567890"])
    client_count: int = Field(examples=[4])
    client_percentage: Decimal = Field(examples=["80.00"])
    clients: list[str] = Field(examples=[["C001", "C002", "C003", "C004"]])


class AnalyticsRead(OrmSchema):
    top_traded_isins: list[TopTradedIsin]
    average_holding_time_per_client: list[ClientAverageHoldingTime]
    most_volatile_client: Optional[MostVolatileClient] = None
    isin_concentration_report: list[IsinConcentrationEntry]
