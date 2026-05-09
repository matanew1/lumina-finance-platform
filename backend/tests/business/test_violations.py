from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from backend.services.violations.rules.sell_before_buy import SellBeforeBuyRule
from backend.services.violations.types import ClientContext, ViolationType


@dataclass
class TransactionRecord:
    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime


def tx(transaction_id: str, action: str, quantity: str, minute: int) -> TransactionRecord:
    return TransactionRecord(
        client_id="C001",
        transaction_id=transaction_id,
        isin="US1234567890",
        action=action,
        quantity=Decimal(quantity),
        price=Decimal("100"),
        timestamp=datetime(2024, 1, 1, 9, 0, 0) + timedelta(minutes=minute),
    )


def test_sell_before_buy_rule_flags_sell_with_no_available_quantity() -> None:
    rule = SellBeforeBuyRule()
    ctx = ClientContext(
        client_id="C001",
        transactions=[
            tx("T1", "sell", "5", minute=0),
            tx("T2", "buy", "2", minute=10),
            tx("T3", "sell", "3", minute=20),
        ],
    )

    drafts = rule.detect(ctx)

    assert [draft.transaction_id for draft in drafts] == ["T1", "T3"]
    assert all(draft.violation_type == ViolationType.SELL_BEFORE_BUY for draft in drafts)
