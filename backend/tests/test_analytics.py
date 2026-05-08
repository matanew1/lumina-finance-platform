from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from backend.db.session import get_db
from backend.main import app
from backend.services.analytics.analytics_service import AnalyticsService


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


@dataclass
class PositionRecord:
    client_id: str
    isin: str
    quantity: Decimal
    market_price: Decimal


class FakeAnalyticsRepository:
    def __init__(self, transactions: list[TransactionRecord], positions: list[PositionRecord]) -> None:
        self.transactions = transactions
        self.positions = positions

    def list_transactions_ordered(self) -> list[TransactionRecord]:
        return sorted(
            self.transactions,
            key=lambda transaction: (transaction.timestamp, transaction.id, transaction.transaction_id),
        )

    def list_current_positions(self) -> list[PositionRecord]:
        return self.positions


class FakeAnalyticsCalculator:
    def __init__(self, report_name: str, value: object) -> None:
        self.report_name = report_name
        self.value = value
        self.received_transactions = []
        self.received_positions = []

    def calculate(self, transactions: list[TransactionRecord], positions: list[PositionRecord]) -> object:
        self.received_transactions = transactions
        self.received_positions = positions
        return self.value


class FakeScalarResult:
    def __init__(self, rows) -> None:
        self.rows = rows

    def all(self):
        return self.rows


class FakeAnalyticsSession:
    def __init__(self, transactions: list[TransactionRecord], positions: list[PositionRecord]) -> None:
        self.rows = [transactions, positions]
        self.index = 0

    def scalars(self, _statement) -> FakeScalarResult:
        rows = self.rows[self.index]
        self.index += 1
        return FakeScalarResult(rows)


def tx(
    transaction_id: str,
    client_id: str,
    isin: str,
    action: str,
    quantity: str,
    price: str,
    day: int,
    row_id: int,
) -> TransactionRecord:
    return TransactionRecord(
        client_id=client_id,
        transaction_id=transaction_id,
        isin=isin,
        action=action,
        quantity=Decimal(quantity),
        price=Decimal(price),
        timestamp=datetime(2024, 1, 1, 9, 0, 0) + timedelta(days=day - 1),
        id=row_id,
    )


def position(client_id: str, isin: str, quantity: str, market_price: str) -> PositionRecord:
    return PositionRecord(
        client_id=client_id,
        isin=isin,
        quantity=Decimal(quantity),
        market_price=Decimal(market_price),
    )


def analytics_fixture() -> tuple[list[TransactionRecord], list[PositionRecord]]:
    transactions = [
        tx("T1", "C001", "ISIN_A", "buy", "10", "10", 1, 1),
        tx("T2", "C001", "ISIN_A", "sell", "5", "12", 2, 2),
        tx("T3", "C001", "ISIN_B", "buy", "1", "100", 3, 3),
        tx("T4", "C002", "ISIN_A", "buy", "2", "20", 1, 4),
        tx("T5", "C002", "ISIN_A", "buy", "1", "40", 2, 5),
        tx("T6", "C003", "ISIN_A", "buy", "1", "30", 1, 6),
    ]
    positions = [
        position("C001", "ISIN_A", "5", "12"),
        position("C001", "ISIN_B", "1", "100"),
        position("C002", "ISIN_A", "3", "40"),
        position("C003", "ISIN_A", "1", "30"),
    ]
    return transactions, positions


def test_analytics_service_computes_required_reports() -> None:
    transactions, positions = analytics_fixture()
    service = AnalyticsService(
        db=FakeAnalyticsSession([], []),
        analytics_repository=FakeAnalyticsRepository(transactions, positions),
    )

    response = service.get_analytics()

    assert response["top_traded_isins"] == [
        {"isin": "ISIN_A", "transaction_count": 5},
        {"isin": "ISIN_B", "transaction_count": 1},
    ]

    holding_by_client = {
        row["client_id"]: row for row in response["average_holding_time_per_client"]
    }
    assert holding_by_client["C001"]["average_holding_seconds"] == Decimal("86400")
    assert holding_by_client["C001"]["average_holding_days"] == Decimal("1.00")
    assert holding_by_client["C001"]["closed_quantity"] == Decimal("5")
    assert holding_by_client["C002"]["average_holding_seconds"] == Decimal("0")

    assert response["most_volatile_client"] == {
        "client_id": "C001",
        "min_portfolio_value": Decimal("60"),
        "max_portfolio_value": Decimal("160"),
        "value_range": Decimal("100"),
    }

    assert response["isin_concentration_report"] == [
        {
            "isin": "ISIN_A",
            "client_count": 3,
            "client_percentage": Decimal("100.00"),
            "clients": ["C001", "C002", "C003"],
        }
    ]


def test_analytics_service_delegates_to_report_calculators() -> None:
    transactions, positions = analytics_fixture()
    calculator = FakeAnalyticsCalculator("custom_report", {"ok": True})
    service = AnalyticsService(
        db=FakeAnalyticsSession([], []),
        analytics_repository=FakeAnalyticsRepository(transactions, positions),
        calculators=[calculator],
    )

    response = service.get_analytics()

    assert response == {"custom_report": {"ok": True}}
    assert [transaction.transaction_id for transaction in calculator.received_transactions] == [
        "T1",
        "T4",
        "T6",
        "T2",
        "T5",
        "T3",
    ]
    assert calculator.received_positions == positions


def test_analytics_endpoint_returns_structured_json() -> None:
    transactions, positions = analytics_fixture()
    fake_db = FakeAnalyticsSession(transactions, positions)

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = TestClient(app).get("/analytics")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["top_traded_isins"][0] == {"isin": "ISIN_A", "transaction_count": 5}
    assert body["average_holding_time_per_client"][0]["client_id"] == "C001"
    assert body["most_volatile_client"]["client_id"] == "C001"
    assert body["isin_concentration_report"][0]["clients"] == ["C001", "C002", "C003"]
