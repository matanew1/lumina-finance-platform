"""
Violation schemas.

A rule is just a plain function: (ClientContext) -> list[ViolationDraft].
No ABC, no class boilerplate — import ViolationRule as the type alias for
that callable signature.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum, auto
from typing import Callable

from pydantic import BaseModel

from backend.app.schemas.shared import PositionView, TransactionView

__all__ = [
    "ClientContext",
    "PositionView",
    "TransactionView",
    "ViolationDraft",
    "ViolationResponse",
    "ViolationRule",
    "ViolationSeverity",
    "ViolationType",
]


class ViolationType(StrEnum):
    # More than 3 buy/sell pairs within 24 hours -> flag as Day Trading
    DAY_TRADING = "Day Trading"
    # One ISIN > 50% of portfolio -> flag as Potential Risk
    RISK_CONCENTRATION = "Potential Risk"
    # Sell Before Buy -> Flag as ERROR (severity)
    SELL_BEFORE_BUY = "Sell Before Buy"
    # Price or Quantity < 0 -> flag as ERROR (severity)
    INVALID_VALUES = "Invalid Values"


class ViolationSeverity(StrEnum):
    ERROR = auto()
    WARNING = auto()


class ViolationDraft(BaseModel):
    """Schema for a detected rule violation."""

    client_id: str
    violation_type: ViolationType
    severity: ViolationSeverity
    message: str
    transaction_id: str | None = None


class ViolationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    client_id: str
    transaction_id: str | None = None
    violation_type: str
    severity: str
    message: str
    created_at: datetime


@dataclass(frozen=True)
class ClientContext:
    """Snapshot of one client's state passed to every rule function."""

    client_id: str
    transactions: list[TransactionView] = field(default_factory=list)
    positions: list[PositionView] = field(default_factory=list)


# A rule is simply a function that inspects a ClientContext and returns
# any violations it finds.  No base class needed.
ViolationRule = Callable[[ClientContext], list[ViolationDraft]]