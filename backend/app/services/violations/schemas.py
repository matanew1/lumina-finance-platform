from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel

from backend.app.services.positions.schemas import PositionSnapshot


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


class ViolationDraft(BaseModel):
    client_id: str
    violation_type: str
    severity: str
    message: str
    transaction_id: str | None = None


@dataclass
class ClientContext:
    client_id: str
    transactions: list[TransactionView] = field(default_factory=list)
    positions: list[PositionSnapshot] = field(default_factory=list)


class ViolationRule(ABC):
    def __call__(self, ctx: ClientContext) -> list[ViolationDraft]:
        return self.evaluate(ctx)

    @abstractmethod
    def evaluate(self, ctx: ClientContext) -> list[ViolationDraft]:
        raise NotImplementedError
