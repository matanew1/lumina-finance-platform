from fastapi.testclient import TestClient

from backend.main import app


def test_openapi_contains_required_endpoints() -> None:
    # TODO: replace this route-registration test with behavior tests once services are implemented.
    client = TestClient(app)
    openapi = client.get("/openapi.json").json()

    assert "/upload-transactions" in openapi["paths"]
    assert "/clients" in openapi["paths"]
    assert "/clients/{client_id}/positions" in openapi["paths"]
    assert "/violations" in openapi["paths"]
    assert "/analytics" in openapi["paths"]
