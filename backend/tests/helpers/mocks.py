from datetime import datetime, timedelta
from decimal import Decimal

from backend.app.models import Position, Transaction, Violation


def transaction(
    transaction_id: str,
    *,
    client_id: str = "C001",
    isin: str = "ISIN001",
    action: str = "buy",
    quantity: Decimal = Decimal("10"),
    price: Decimal = Decimal("100"),
    minutes: int = 0,
) -> Transaction:
    return Transaction(
        client_id=client_id,
        transaction_id=transaction_id,
        isin=isin,
        action=action,
        quantity=quantity,
        price=price,
        timestamp=datetime(2024, 1, 1, 9, 0, 0) + timedelta(minutes=minutes),
    )


def position(
    *,
    client_id: str = "C001",
    isin: str = "ISIN001",
    quantity: Decimal = Decimal("10"),
    average_price: Decimal = Decimal("100"),
    market_price: Decimal = Decimal("105"),
    realized_pnl: Decimal = Decimal("5"),
    unrealized_pnl: Decimal = Decimal("50"),
) -> Position:
    return Position(
        client_id=client_id,
        isin=isin,
        quantity=quantity,
        average_price=average_price,
        market_price=market_price,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
    )


def violation(
    *,
    client_id: str = "C001",
    transaction_id: str | None = None,
    violation_type: str = "risk_concentration",
    severity: str = "warning",
    message: str = "Client has concentrated exposure.",
) -> Violation:
    return Violation(
        client_id=client_id,
        transaction_id=transaction_id,
        violation_type=violation_type,
        severity=severity,
        message=message,
    )
