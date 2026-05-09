from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from backend.services.positions.fifo_calculator import FifoCalculator


@dataclass
class TransactionRecord:
    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    id: int


def tx(transaction_id: str, action: str, quantity: str, price: str, day: int, row_id: int) -> TransactionRecord:
    return TransactionRecord(
        client_id="C001",
        transaction_id=transaction_id,
        isin="US1234567890",
        action=action,
        quantity=Decimal(quantity),
        price=Decimal(price),
        timestamp=datetime(2024, 1, day, 10, 0, 0),
        id=row_id,
    )


def test_fifo_calculation_uses_oldest_purchase_lots() -> None:
    positions = FifoCalculator().calculate(
        [
            tx("T1", "buy", "10", "100", day=1, row_id=1),
            tx("T2", "buy", "10", "110", day=2, row_id=2),
            tx("T3", "sell", "15", "120", day=3, row_id=3),
        ]
    )

    assert positions == [
        {
            "client_id": "C001",
            "isin": "US1234567890",
            "quantity": Decimal("5"),
            "average_cost": Decimal("110"),
            "market_price": Decimal("120"),
            "realized_pnl": Decimal("250"),
            "unrealized_pnl": Decimal("50"),
        }
    ]
