from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from backend.db.session import get_db
from backend.main import app
from backend.services.positions.fifo_calculator import calculate_fifo_positions
from backend.services.positions.position_service import PositionService


@dataclass
class TransactionRecord:
    client_id: str
    transaction_id: str
    isin: str
    action: str
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    id: int = 1


@dataclass
class PositionRecord:
    client_id: str
    isin: str
    quantity: Decimal
    average_price: Decimal
    market_price: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal


class FakePositionRepository:
    def __init__(self, positions: list[PositionRecord]) -> None:
        self.positions = positions

    def list_client_positions(self, client_id: str) -> list[PositionRecord]:
        return [position for position in self.positions if position.client_id == client_id]


class FakeScalarResult:
    def __init__(self, rows: list[TransactionRecord]) -> None:
        self.rows = rows

    def all(self) -> list[TransactionRecord]:
        return self.rows


class FakeReadSession:
    def __init__(self, rows: list[TransactionRecord] | list[PositionRecord]) -> None:
        self.rows = rows

    def scalars(self, _statement) -> FakeScalarResult:
        return FakeScalarResult(self.rows)


def tx(
    transaction_id: str,
    action: str,
    quantity: str,
    price: str,
    *,
    isin: str = "US1234567890",
    client_id: str = "C001",
    day: int = 1,
    row_id: int = 1,
) -> TransactionRecord:
    return TransactionRecord(
        id=row_id,
        client_id=client_id,
        transaction_id=transaction_id,
        isin=isin,
        action=action,
        quantity=Decimal(quantity),
        price=Decimal(price),
        timestamp=datetime(2023, 11, day, 10, 0, 0),
    )


def persisted_position(
    *,
    client_id: str = "C001",
    isin: str = "US1234567890",
    quantity: str = "30",
    average_price: str = "100.5",
    market_price: str = "105.2",
    realized_pnl: str = "94.0",
    unrealized_pnl: str = "141.0",
) -> PositionRecord:
    return PositionRecord(
        client_id=client_id,
        isin=isin,
        quantity=Decimal(quantity),
        average_price=Decimal(average_price),
        market_price=Decimal(market_price),
        realized_pnl=Decimal(realized_pnl),
        unrealized_pnl=Decimal(unrealized_pnl),
    )


def test_fifo_calculation_uses_oldest_purchase_batches_for_realized_pnl() -> None:
    positions = calculate_fifo_positions(
        [
            tx("T1", "buy", "10", "100", day=1, row_id=1),
            tx("T2", "buy", "10", "110", day=2, row_id=2),
            tx("T3", "sell", "15", "120", day=3, row_id=3),
        ]
    )

    assert len(positions) == 1
    position = positions[0]
    assert position["quantity"] == Decimal("5")
    assert position["average_cost"] == Decimal("110")
    assert position["market_price"] == Decimal("120")
    assert position["realized_pnl"] == Decimal("250")
    assert position["unrealized_pnl"] == Decimal("50")


def test_fifo_calculation_rejects_sell_quantity_above_available_position() -> None:
    with pytest.raises(ValueError, match="exceeds available position"):
        calculate_fifo_positions(
            [
                tx("T1", "buy", "5", "100", day=1, row_id=1),
                tx("T2", "sell", "6", "110", day=2, row_id=2),
            ]
        )


def test_position_service_returns_positions_per_isin_and_totals() -> None:
    service = PositionService(
        db=FakeReadSession([]),
        position_repository=FakePositionRepository(
            [
                persisted_position(),
                persisted_position(
                    isin="US9999999999",
                    quantity="10",
                    average_price="98",
                    market_price="98",
                    realized_pnl="0",
                    unrealized_pnl="0",
                ),
            ]
        ),
    )

    response = service.get_client_positions("C001")

    assert response["client_id"] == "C001"
    assert len(response["positions"]) == 2
    first_position = response["positions"][0]
    second_position = response["positions"][1]
    assert first_position["isin"] == "US1234567890"
    assert first_position["quantity"] == Decimal("30")
    assert first_position["average_cost"] == Decimal("100.5")
    assert first_position["realized_pnl"] == Decimal("94.0")
    assert first_position["unrealized_pnl"] == Decimal("141.0")
    assert second_position["isin"] == "US9999999999"
    assert second_position["quantity"] == Decimal("10")
    assert second_position["unrealized_pnl"] == Decimal("0")
    assert response["total_realized_pnl"] == Decimal("94.0")
    assert response["total_unrealized_pnl"] == Decimal("141.0")


def test_client_positions_endpoint_returns_fifo_pnl_response() -> None:
    fake_db = FakeReadSession(
        [
            persisted_position(
                quantity="5",
                average_price="100",
                market_price="130",
                realized_pnl="150",
                unrealized_pnl="150",
            ),
        ]
    )

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = TestClient(app).get("/clients/C001/positions")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["client_id"] == "C001"
    assert body["positions"][0]["isin"] == "US1234567890"
    assert body["positions"][0]["quantity"] == "5"
    assert body["positions"][0]["realized_pnl"] == "150"
    assert body["positions"][0]["unrealized_pnl"] == "150"
