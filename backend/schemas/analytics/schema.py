from decimal import Decimal

from pydantic import BaseModel


class TopTradedIsin(BaseModel):
    isin: str
    transaction_count: int


class ClientAverageHoldingTime(BaseModel):
    client_id: str
    average_holding_seconds: Decimal
    average_holding_days: Decimal
    closed_quantity: Decimal


class MostVolatileClient(BaseModel):
    client_id: str
    min_portfolio_value: Decimal
    max_portfolio_value: Decimal
    value_range: Decimal


class IsinConcentrationEntry(BaseModel):
    isin: str
    client_count: int
    client_percentage: Decimal
    clients: list[str]


class AnalyticsResponse(BaseModel):
    top_traded_isins: list[TopTradedIsin]
    average_holding_time_per_client: list[ClientAverageHoldingTime]
    most_volatile_client: MostVolatileClient | None = None
    isin_concentration_report: list[IsinConcentrationEntry]
