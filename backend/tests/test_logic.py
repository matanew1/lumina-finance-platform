from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

import pandas as pd

from backend.app.services.positions.helpers.fifo_engine import calculate_fifo_positions
from backend.app.services.violations import (
    ClientContext,
    ViolationType,
    detect_sell_before_buy,
)
from backend.app.services.transactions.helpers.dataframe import (
    normalize_transaction_dataframe,
    validate_transaction_dataframe,
)


@dataclass
class TransactionRecord:
    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    id: int = 0


def tx(
    transaction_id: str,
    action: str,
    quantity: str,
    price: str = "100",
    minute: int = 0,
    row_id: int = 0,
) -> TransactionRecord:
    return TransactionRecord(
        client_id="C001",
        transaction_id=transaction_id,
        isin="US1234567890",
        action=action,
        quantity=Decimal(quantity),
        price=Decimal(price),
        timestamp=datetime(2024, 1, 1, 9, 0, 0) + timedelta(minutes=minute),
        id=row_id,
    )


def test_fifo_calculates_realized_and_unrealized_pnl() -> None:
    positions = calculate_fifo_positions(
        [
            tx("T1", "buy", "10", "100", row_id=1),
            tx("T2", "buy", "10", "110", minute=10, row_id=2),
            tx("T3", "sell", "15", "120", minute=20, row_id=3),
        ]
    )

    assert positions[0].model_dump() == {
        "client_id": "C001",
        "isin": "US1234567890",
        "quantity": Decimal("5"),
        "average_cost": Decimal("110"),
        "market_price": Decimal("120"),
        "realized_pnl": Decimal("250"),
        "unrealized_pnl": Decimal("50"),
    }


def test_sell_before_buy_rule_flags_uncovered_sell() -> None:
    context = ClientContext(
        client_id="C001",
        transactions=[
            tx("T1", "sell", "5"),
            tx("T2", "buy", "2", minute=10),
            tx("T3", "sell", "3", minute=20),
        ],
    )

    drafts = detect_sell_before_buy(context)

    assert [draft.transaction_id for draft in drafts] == ["T1", "T3"]
    assert all(draft.violation_type == ViolationType.SELL_BEFORE_BUY for draft in drafts)


def test_upload_validation_rejects_invalid_rows() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "ClientId": "C001",
                "TransactionId": "T1001",
                "ISIN": "US1234567890",
                "Action": "Hold",
                "Quantity": 0,
                "Price": -1,
                "Timestamp": "not-a-date",
            }
        ]
    )

    errors = validate_transaction_dataframe(normalize_transaction_dataframe(dataframe))
    fields = {error.field for error in errors}

    assert {"action", "quantity", "price", "timestamp"}.issubset(fields)
