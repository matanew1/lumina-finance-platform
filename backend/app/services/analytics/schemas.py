from datetime import datetime
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel


class TransactionView(Protocol):
    client_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime


class PositionView(Protocol):
    client_id: str
    isin: str
    quantity: Decimal


class TopTradedIsinResult(BaseModel):
    isin: str
    transaction_count: int


class ClientAverageHoldingTimeResult(BaseModel):
    client_id: str
    average_holding_seconds: Decimal
    average_holding_days: Decimal
    closed_quantity: Decimal


class MostVolatileClientResult(BaseModel):
    client_id: str
    min_portfolio_value: Decimal
    max_portfolio_value: Decimal
    value_range: Decimal


class IsinConcentrationResult(BaseModel):
    isin: str
    client_count: int
    client_percentage: Decimal
    clients: list[str]


class AnalyticsResult(BaseModel):
    top_traded_isins: list[TopTradedIsinResult]
    average_holding_time_per_client: list[ClientAverageHoldingTimeResult]
    most_volatile_client: MostVolatileClientResult | None = None
    isin_concentration_report: list[IsinConcentrationResult]


class HoldingLot(BaseModel):
    quantity: Decimal
    timestamp: datetime
