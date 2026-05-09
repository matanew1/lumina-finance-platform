"""
Analytics schemas.

Result models are the single source of truth for both the service layer
(computation) and the API layer (serialisation).  The API schema module
(backend.app.schemas.analytics) simply re-exports these classes.

Protocol types live in shared.protocols and are imported here so callers
that previously imported TransactionView/PositionView from this module
continue to work without changes.
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from backend.app.schemas.shared import PositionView, TransactionView

__all__ = [
    # Protocols (re-exported for backwards compatibility)
    "TransactionView",
    "PositionView",
    # Internal helper
    "HoldingLot",
    # Result / response models (single source of truth)
    "TopTradedIsin",
    "ClientAverageHoldingTime",
    "MostVolatileClient",
    "IsinConcentrationEntry",
    "AnalyticsResponse",
]


# ── internal helper ────────────────────────────────────────────────────────────

class HoldingLot(BaseModel):
    quantity: Decimal
    timestamp: datetime


# ── result / response models ───────────────────────────────────────────────────

class TopTradedIsin(BaseModel):
    """Top-traded ISIN by transaction count."""

    model_config = ConfigDict(from_attributes=True)

    isin: str
    transaction_count: int


class ClientAverageHoldingTime(BaseModel):
    """Average holding time (in seconds and days) for a client."""

    model_config = ConfigDict(from_attributes=True)

    client_id: str
    average_holding_seconds: Decimal
    average_holding_days: Decimal
    closed_quantity: Decimal


class MostVolatileClient(BaseModel):
    """Client whose portfolio value swung the most."""

    model_config = ConfigDict(from_attributes=True)

    client_id: str
    min_portfolio_value: Decimal
    max_portfolio_value: Decimal
    value_range: Decimal


class IsinConcentrationEntry(BaseModel):
    """ISIN held by a disproportionately large share of clients."""

    model_config = ConfigDict(from_attributes=True)

    isin: str
    client_count: int
    client_percentage: Decimal
    clients: list[str]


class AnalyticsResponse(BaseModel):
    """Aggregated analytics report returned to callers."""

    model_config = ConfigDict(from_attributes=True)

    top_traded_isins: list[TopTradedIsin]
    average_holding_time_per_client: list[ClientAverageHoldingTime]
    most_volatile_client: MostVolatileClient | None = None
    isin_concentration_report: list[IsinConcentrationEntry]
