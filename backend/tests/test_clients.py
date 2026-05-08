from fastapi.testclient import TestClient

from backend.db.session import get_db
from backend.main import app
from backend.services.client_service import ClientService


class FakeClientRepository:
    def __init__(self, client_ids: list[str]) -> None:
        self.client_ids = client_ids

    def list_client_ids(self) -> list[str]:
        return self.client_ids


class FakeScalarResult:
    def __init__(self, rows: list[str]) -> None:
        self.rows = rows

    def all(self) -> list[str]:
        return self.rows


class FakeReadSession:
    def __init__(self, rows: list[str]) -> None:
        self.rows = rows

    def scalars(self, _statement) -> FakeScalarResult:
        return FakeScalarResult(self.rows)


def test_client_service_returns_client_records() -> None:
    service = ClientService(
        db=FakeReadSession([]),
        client_repository=FakeClientRepository(["C001", "C002"]),
    )

    assert service.get_clients() == [{"client_id": "C001"}, {"client_id": "C002"}]


def test_get_clients_endpoint_returns_distinct_clients() -> None:
    fake_db = FakeReadSession(["C001", "C002"])

    def override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = override_get_db

    try:
        response = TestClient(app).get("/clients")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [{"client_id": "C001"}, {"client_id": "C002"}]
