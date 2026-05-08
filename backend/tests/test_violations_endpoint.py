from datetime import datetime
from io import BytesIO
from typing import Optional

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.db.session import get_db
from backend.main import app
from backend.services.transactions.transaction_service import TransactionService


class FakeUploadFile:
    def __init__(self, filename: str, contents: bytes) -> None:
        self.filename = filename
        self._contents = contents

    async def read(self) -> bytes:
        return self._contents


class FakeViolationRecord:
    def __init__(
        self,
        *,
        id: int,
        client_id: str,
        violation_type: str,
        severity: str,
        message: str,
        transaction_id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        self.id = id
        self.client_id = client_id
        self.violation_type = violation_type
        self.severity = severity
        self.message = message
        self.transaction_id = transaction_id
        self.created_at = created_at or datetime(2024, 1, 1, 12, 0, 0)


class FakeScalarResult:
    def __init__(self, rows) -> None:
        self.rows = rows

    def all(self):
        return self.rows


class FakeUploadSession:
    def __init__(self) -> None:
        self.added: list = []
        self.committed = False
        self.rolled_back = False

    def add_all(self, items) -> None:
        self.added.extend(items)

    def execute(self, _statement) -> None:
        return None

    def flush(self) -> None:
        return None

    def scalars(self, _statement) -> FakeScalarResult:
        transactions = [item for item in self.added if item.__class__.__name__ == "Transaction"]
        return FakeScalarResult(transactions)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class FakeViolationListSession:
    def __init__(self, rows: list[FakeViolationRecord]) -> None:
        self.rows = rows

    def scalars(self, _statement) -> FakeScalarResult:
        return FakeScalarResult(self.rows)


def workbook_bytes(rows: list[dict]) -> bytes:
    buffer = BytesIO()
    pd.DataFrame(rows).to_excel(buffer, index=False)
    return buffer.getvalue()


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_upload_persists_day_trading_violation_for_excessive_pairs() -> None:
    session = FakeUploadSession()
    rows = []
    base = datetime(2024, 1, 1, 9, 0, 0)
    for i in range(4):
        rows.append({
            "ClientId": "C001",
            "TransactionId": f"B{i}",
            "ISIN": "US1234567890",
            "Action": "Buy",
            "Quantity": 1,
            "Price": 100,
            "Timestamp": (base.replace(minute=10 * i)).isoformat(),
        })
        rows.append({
            "ClientId": "C001",
            "TransactionId": f"S{i}",
            "ISIN": "US1234567890",
            "Action": "Sell",
            "Quantity": 1,
            "Price": 100,
            "Timestamp": (base.replace(minute=10 * i + 5)).isoformat(),
        })

    response = await TransactionService(db=session).upload_transactions(
        FakeUploadFile("transactions.xlsx", workbook_bytes(rows))
    )
    violations = [item for item in session.added if item.__class__.__name__ == "Violation"]

    assert response["status"] == "success"
    day_trading_violations = [
        violation for violation in violations if violation.violation_type == "DAY_TRADING"
    ]
    assert day_trading_violations
    assert all(violation.transaction_id is not None for violation in day_trading_violations)


@pytest.mark.anyio
async def test_upload_persists_risk_concentration_violation_for_concentrated_portfolio() -> None:
    session = FakeUploadSession()
    rows = [
        {
            "ClientId": "C001",
            "TransactionId": "T1",
            "ISIN": "ISIN_A",
            "Action": "Buy",
            "Quantity": 10,
            "Price": 70,
            "Timestamp": "2024-01-01T09:00:00",
        },
        {
            "ClientId": "C001",
            "TransactionId": "T2",
            "ISIN": "ISIN_B",
            "Action": "Buy",
            "Quantity": 10,
            "Price": 30,
            "Timestamp": "2024-01-01T10:00:00",
        },
    ]

    response = await TransactionService(db=session).upload_transactions(
        FakeUploadFile("transactions.xlsx", workbook_bytes(rows))
    )
    violations = [item for item in session.added if item.__class__.__name__ == "Violation"]

    assert response["status"] == "success"
    risk_violations = [
        violation
        for violation in violations
        if violation.violation_type == "RISK_CONCENTRATION" and "ISIN_A" in violation.message
    ]
    assert risk_violations
    assert risk_violations[0].transaction_id == "T1"


def test_get_violations_endpoint_returns_persisted_violations() -> None:
    fake_db = FakeViolationListSession(
        [
            FakeViolationRecord(
                id=1,
                client_id="C001",
                violation_type="DAY_TRADING",
                severity="WARNING",
                message="4 buy/sell pairs of US1234567890 within 24h (limit: 3).",
            ),
            FakeViolationRecord(
                id=2,
                client_id="C002",
                violation_type="RISK_CONCENTRATION",
                severity="WARNING",
                message="ISIN_A is 70.00% of portfolio (threshold: 50%).",
            ),
        ]
    )

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).get("/violations")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {entry["violation_type"] for entry in body} == {"DAY_TRADING", "RISK_CONCENTRATION"}
