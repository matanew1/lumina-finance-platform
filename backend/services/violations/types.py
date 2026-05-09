from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Protocol


class ViolationType:
    DAY_TRADING = "DAY_TRADING"
    RISK_CONCENTRATION = "RISK_CONCENTRATION"
    SELL_BEFORE_BUY = "SELL_BEFORE_BUY"
    INVALID_VALUES = "INVALID_VALUES"


class ViolationSeverity:
    ERROR = "ERROR"
    WARNING = "WARNING"


class TransactionView(Protocol):
    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime


class PositionView(Protocol):
    client_id: str
    isin: str
    quantity: Decimal
    market_price: Decimal
    transaction_id: Optional[str]


@dataclass(frozen=True)
class PositionSnapshot:
    client_id: str
    isin: str
    quantity: Decimal
    market_price: Decimal
    transaction_id: Optional[str] = None


@dataclass(frozen=True)
class ViolationDraft:
    client_id: str
    violation_type: str
    severity: str
    message: str
    transaction_id: Optional[str] = None


@dataclass
class ClientContext:
    client_id: str
    transactions: list[TransactionView] = field(default_factory=list)
    positions: list[PositionSnapshot] = field(default_factory=list)
