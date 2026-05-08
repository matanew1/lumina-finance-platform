from io import BytesIO
from decimal import Decimal

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from backend.db.session import get_db
from backend.main import app
from backend.services.transactions.transaction_service import TransactionService
from backend.utils.exceptions import BadRequestError


class FakeUploadFile:
    def __init__(self, filename: str, contents: bytes) -> None:
        self.filename = filename
        self._contents = contents

    async def read(self) -> bytes:
        return self._contents


class FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.committed = False
        self.rolled_back = False
        self.executed = []

    def add_all(self, items) -> None:
        self.added.extend(items)

    def execute(self, statement) -> None:
        self.executed.append(statement)

    def flush(self) -> None:
        return None

    def scalars(self, _statement):
        transactions = [item for item in self.added if item.__class__.__name__ == "Transaction"]
        return FakeScalarResult(transactions)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


class DuplicateTransactionSession(FakeSession):
    def commit(self) -> None:
        raise IntegrityError(
            statement="INSERT INTO transactions",
            params={},
            orig=Exception('duplicate key value violates unique constraint "ix_transactions_transaction_id"'),
        )


class FakeScalarResult:
    def __init__(self, rows) -> None:
        self.rows = rows

    def all(self):
        return self.rows


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def fake_session() -> FakeSession:
    return FakeSession()


@pytest.fixture
def duplicate_transaction_session() -> DuplicateTransactionSession:
    return DuplicateTransactionSession()


@pytest.fixture #
def client() -> TestClient:
    return TestClient(app)


def workbook_bytes(rows: list[dict]) -> bytes:
    buffer = BytesIO()
    pd.DataFrame(rows).to_excel(buffer, index=False)
    return buffer.getvalue()


def csv_bytes(rows: list[dict]) -> bytes:
    return pd.DataFrame(rows).to_csv(index=False).encode()


@pytest.mark.anyio
async def test_upload_transactions_normalizes_valid_rows_and_persists(fake_session: FakeSession) -> None:
    file = FakeUploadFile(
        "transactions.xlsx",
        workbook_bytes(
            [
                {
                    "ClientId": " C001 ",
                    "TransactionId": " T1001 ",
                    "ISIN": " US1234567890 ",
                    "Action": "Buy",
                    "Quantity": 50,
                    "Price": 100.5,
                    "Timestamp": "2023-11-01T10:00:00",
                },
                {
                    "ClientId": "C001",
                    "TransactionId": "T1002",
                    "ISIN": "US1234567890",
                    "Action": " sell ",
                    "Quantity": 20,
                    "Price": 105.2,
                    "Timestamp": "2023-11-05T11:00:00",
                },
            ]
        ),
    )

    response = await TransactionService(db=fake_session).upload_transactions(file=file)

    assert response["status"] == "success"
    assert response["total_rows"] == 2
    assert response["valid_rows"] == 2
    assert response["invalid_rows"] == 0
    assert response["persisted_rows"] == 2
    assert "transactions" not in response
    assert fake_session.committed is True
    transactions = [item for item in fake_session.added if item.__class__.__name__ == "Transaction"]
    positions = [item for item in fake_session.added if item.__class__.__name__ == "Position"]
    assert len(transactions) == 2
    assert transactions[0].client_id == "C001"
    assert transactions[0].action == "buy"
    assert transactions[1].action == "sell"
    assert len(positions) == 1
    assert positions[0].client_id == "C001"
    assert positions[0].isin == "US1234567890"
    assert positions[0].quantity == Decimal("30")
    assert positions[0].average_price == Decimal("100.5")


@pytest.mark.anyio
async def test_upload_transactions_returns_validation_errors_without_persisting(fake_session: FakeSession) -> None:
    file = FakeUploadFile(
        "transactions.xlsx",
        workbook_bytes(
            [
                {
                    "ClientId": "C001",
                    "TransactionId": "T1001",
                    "ISIN": "US1234567890",
                    "Action": "Hold",
                    "Quantity": 0,
                    "Price": 0,
                    "Timestamp": "2023-11-01T10:00:00",
                }
            ]
        ),
    )

    response = await TransactionService(db=fake_session).upload_transactions(file=file)
    error_fields = {error["field"] for error in response["errors"]}

    assert response["status"] == "failed"
    assert response["total_rows"] == 1
    assert response["valid_rows"] == 0
    assert response["invalid_rows"] == 1
    assert response["persisted_rows"] == 0
    assert "transactions" not in response
    assert {"action", "quantity", "price"}.issubset(error_fields)
    assert fake_session.added == []
    assert fake_session.committed is False


@pytest.mark.anyio
async def test_upload_transactions_rebuilds_positions_chronologically(fake_session: FakeSession) -> None:
    file = FakeUploadFile(
        "transactions.csv",
        csv_bytes(
            [
                {
                    "ClientId": "C001",
                    "TransactionId": "T3002",
                    "ISIN": "US1234567890",
                    "Action": "Sell",
                    "Quantity": 5,
                    "Price": 130,
                    "Timestamp": "2023-11-02T10:00:00",
                },
                {
                    "ClientId": "C001",
                    "TransactionId": "T3001",
                    "ISIN": "US1234567890",
                    "Action": "Buy",
                    "Quantity": 10,
                    "Price": 100,
                    "Timestamp": "2023-11-01T10:00:00",
                },
            ]
        ),
    )

    response = await TransactionService(db=fake_session).upload_transactions(file=file)
    positions = [item for item in fake_session.added if item.__class__.__name__ == "Position"]

    assert response["status"] == "success"
    assert "transactions" not in response
    assert len(positions) == 1
    assert positions[0].client_id == "C001"
    assert positions[0].isin == "US1234567890"
    assert positions[0].quantity == Decimal("5")
    assert positions[0].average_price == Decimal("100")


@pytest.mark.anyio
async def test_upload_transactions_rolls_back_when_fifo_rules_fail(fake_session: FakeSession) -> None:
    file = FakeUploadFile(
        "transactions.csv",
        csv_bytes(
            [
                {
                    "ClientId": "C001",
                    "TransactionId": "T4001",
                    "ISIN": "US1234567890",
                    "Action": "Sell",
                    "Quantity": 5,
                    "Price": 130,
                    "Timestamp": "2023-11-02T10:00:00",
                }
            ]
        ),
    )

    with pytest.raises(BadRequestError, match="exceeds available position"):
        await TransactionService(db=fake_session).upload_transactions(file=file)

    assert fake_session.rolled_back is True
    assert fake_session.committed is False


def test_upload_transactions_endpoint_returns_201_for_structured_response(
    client: TestClient,
    fake_session: FakeSession,
) -> None:
    def override_get_db():
        yield fake_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/upload-transactions",
            files={
                "file": (
                    "transactions.xlsx",
                    workbook_bytes(
                        [
                            {
                                "ClientId": "C002",
                                "TransactionId": "T2001",
                                "ISIN": "US0987654321",
                                "Action": "Buy",
                                "Quantity": 100,
                                "Price": 80,
                                "Timestamp": "2023-11-03T09:00:00",
                            }
                        ]
                    ),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "total_rows": 1,
        "valid_rows": 1,
        "invalid_rows": 0,
        "persisted_rows": 1,
        "errors": [],
    }


def test_upload_transactions_endpoint_returns_409_for_duplicate_transaction_id(
    client: TestClient,
    duplicate_transaction_session: DuplicateTransactionSession,
) -> None:
    def override_get_db():
        yield duplicate_transaction_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = client.post(
            "/upload-transactions",
            files={
                "file": (
                    "transactions.xlsx",
                    workbook_bytes(
                        [
                            {
                                "ClientId": "C002",
                                "TransactionId": "T2001",
                                "ISIN": "US0987654321",
                                "Action": "Buy",
                                "Quantity": 100,
                                "Price": 80,
                                "Timestamp": "2023-11-03T09:00:00",
                            }
                        ]
                    ),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    assert response.json()["detail"] == "One or more transactions have duplicate transaction IDs."
    assert duplicate_transaction_session.rolled_back is True


def test_upload_transactions_endpoint_returns_400_for_unsupported_file(client: TestClient) -> None:
    response = client.post(
        "/upload-transactions",
        files={"file": ("transactions.txt", b"not,a,supported,file", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only .csv or .xlsx transaction files are supported."
