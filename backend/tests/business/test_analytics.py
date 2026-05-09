from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from backend.services.analytics.reports import AnalyticsReports


@dataclass
class TransactionRecord:
    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime


def tx(transaction_id: str, isin: str) -> TransactionRecord:
    return TransactionRecord(
        client_id="C001",
        transaction_id=transaction_id,
        isin=isin,
        action="buy",
        quantity=Decimal("1"),
        price=Decimal("100"),
        timestamp=datetime(2024, 1, 1, 10, 0, 0),
    )


def test_top_traded_isins_are_sorted_by_count_then_isin() -> None:
    report = AnalyticsReports().top_traded_isins(
        [
            tx("T1", "ISIN_B"),
            tx("T2", "ISIN_A"),
            tx("T3", "ISIN_B"),
            tx("T4", "ISIN_A"),
            tx("T5", "ISIN_C"),
        ],
    )

    assert report == [
        {"isin": "ISIN_A", "transaction_count": 2},
        {"isin": "ISIN_B", "transaction_count": 2},
        {"isin": "ISIN_C", "transaction_count": 1},
    ]
