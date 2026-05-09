from datetime import datetime
from decimal import Decimal
from typing import Optional, Protocol

from pydantic import BaseModel


class PositionRecord(Protocol):
    client_id: str
    isin: str
    quantity: Decimal
    average_price: Decimal
    market_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    updated_at: datetime


class PositionRepository(Protocol):
    def list_client_positions(self, client_id: str) -> list[PositionRecord]: ...


class TransactionView(Protocol):
    client_id: str
    transaction_id: str
    isin: str


class PositionView(Protocol):
    client_id: str
    isin: str
    quantity: Decimal
    market_price: Decimal
    transaction_id: Optional[str]


class PositionSnapshot(BaseModel):
    client_id: str
    isin: str
    quantity: Decimal
    market_price: Decimal
    transaction_id: str | None = None
