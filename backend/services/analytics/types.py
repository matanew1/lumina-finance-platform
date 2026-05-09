from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol, TypeAlias


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


AnalyticsResponse: TypeAlias = dict[str, Any]
ReportRow: TypeAlias = dict[str, Any]


@dataclass
class HoldingLot:
    quantity: Decimal
    timestamp: datetime
