from decimal import Decimal

from pydantic import BaseModel, ConfigDict

# Analytics Schemas
class TopTradedIsin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    isin: str
    transaction_count: int
class ClientAverageHoldingTime(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    client_id: str
    average_holding_seconds: Decimal
    average_holding_days: Decimal
    closed_quantity: Decimal
class MostVolatileClient(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    client_id: str
    min_portfolio_value: Decimal
    max_portfolio_value: Decimal
    value_range: Decimal
class IsinConcentrationEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    isin: str
    client_count: int
    client_percentage: Decimal
    clients: list[str]


# Main Analytics Response Model
class AnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    top_traded_isins: list[TopTradedIsin]
    average_holding_time_per_client: list[ClientAverageHoldingTime]
    most_volatile_client: MostVolatileClient | None = None
    isin_concentration_report: list[IsinConcentrationEntry]
