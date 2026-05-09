"""
Shared structural Protocol types used across multiple services.

These Protocols describe the minimal interface each service requires from
domain objects.  Any concrete class (ORM model, Pydantic model, dataclass …)
that satisfies the structural typing is accepted without explicit inheritance.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class TransactionView(Protocol):
    """Full transaction interface required by violation detection and analytics."""

    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime


@runtime_checkable
class PositionView(Protocol):
    """Position interface required by analytics and position helpers."""

    client_id: str
    isin: str
    quantity: Decimal
    market_price: Decimal
    transaction_id: Optional[str]
