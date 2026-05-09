from decimal import Decimal

from backend.tests.helpers.api import (
    as_decimal,
    duplicate_transaction_upload_csv,
    seed,
    upload_csv,
    valid_upload_csv,
)
from backend.tests.helpers.mocks import position, transaction, violation


def test_upload_transactions_endpoint_returns_201_on_successful_upload(api_client) -> None:
    client, _session_factory = api_client

    response = upload_csv(client, valid_upload_csv())

    assert response.status_code == 201
    assert response.json() == {
        "status": "success",
        "total_rows": 2,
        "valid_rows": 2,
        "invalid_rows": 0,
        "persisted_rows": 2,
        "errors": [],
    }


def test_upload_transactions_endpoint_returns_400_on_invalid_csv(api_client) -> None:
    client, _session_factory = api_client

    response = upload_csv(client, "not_a_transaction_column\nvalue")

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "Missing required transaction columns: client_id, transaction_id, "
            "isin, action, quantity, price, timestamp."
        )
    }


def test_upload_transactions_endpoint_returns_409_on_duplicate_transaction_id(
    api_client,
) -> None:
    client, _session_factory = api_client

    response = upload_csv(client, duplicate_transaction_upload_csv())

    assert response.status_code == 409
    assert response.json() == {
        "detail": "One or more transactions have duplicate transaction IDs."
    }


def test_clients_endpoint_returns_200_with_clients_from_database_dependency(
    api_client,
) -> None:
    client, session_factory = api_client
    seed(
        session_factory,
        transaction("T001", client_id="C002"),
        transaction("T002", client_id="C001"),
    )

    response = client.get("/clients")

    assert response.status_code == 200
    assert response.json() == [{"client_id": "C001"}, {"client_id": "C002"}]


def test_clients_endpoint_returns_200_with_empty_list_when_no_clients(api_client) -> None:
    client, _session_factory = api_client

    response = client.get("/clients")

    assert response.status_code == 200
    assert response.json() == []


def test_client_positions_endpoint_returns_200_with_positions_from_database_dependency(
    api_client,
) -> None:
    client, session_factory = api_client
    seed(session_factory, position())

    response = client.get("/clients/C001/positions")

    assert response.status_code == 200
    payload = response.json()
    assert payload["client_id"] == "C001"
    assert len(payload["positions"]) == 1
    assert payload["positions"][0]["isin"] == "ISIN001"
    assert as_decimal(payload["positions"][0]["quantity"]) == Decimal("10")
    assert as_decimal(payload["positions"][0]["average_cost"]) == Decimal("100")
    assert as_decimal(payload["total_realized_pnl"]) == Decimal("5")
    assert as_decimal(payload["total_unrealized_pnl"]) == Decimal("50")


def test_client_positions_endpoint_returns_200_with_empty_list_when_no_positions(
    api_client,
) -> None:
    client, _session_factory = api_client

    response = client.get("/clients/C001/positions")

    assert response.status_code == 200
    assert response.json()["positions"] == []
    assert as_decimal(response.json()["total_realized_pnl"]) == Decimal("0")
    assert as_decimal(response.json()["total_unrealized_pnl"]) == Decimal("0")


def test_violations_endpoint_returns_200_with_violations_from_database_dependency(
    api_client,
) -> None:
    client, session_factory = api_client
    seed(session_factory, violation())

    response = client.get("/violations")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["client_id"] == "C001"
    assert response.json()[0]["violation_type"] == "risk_concentration"
    assert response.json()[0]["severity"] == "warning"


def test_violations_endpoint_returns_200_with_empty_list_when_no_violations(
    api_client,
) -> None:
    client, _session_factory = api_client

    response = client.get("/violations")

    assert response.status_code == 200
    assert response.json() == []


def test_analytics_endpoint_returns_200_with_analytics_from_database_dependency(
    api_client,
) -> None:
    client, session_factory = api_client
    seed(
        session_factory,
        transaction("T001", action="buy", quantity=Decimal("10"), minutes=0),
        transaction(
            "T002",
            action="sell",
            quantity=Decimal("4"),
            price=Decimal("110"),
            minutes=60,
        ),
        transaction(
            "T003",
            client_id="C002",
            action="buy",
            quantity=Decimal("5"),
            price=Decimal("90"),
            minutes=120,
        ),
        position(client_id="C001", quantity=Decimal("6")),
        position(client_id="C002", quantity=Decimal("5")),
    )

    response = client.get("/analytics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["top_traded_isins"] == [
        {"isin": "ISIN001", "transaction_count": 3}
    ]
    average_holding_client_ids = {
        entry["client_id"] for entry in payload["average_holding_time_per_client"]
    }
    assert average_holding_client_ids == {
        "C001",
        "C002",
    }
    assert payload["most_volatile_client"]["client_id"] == "C001"
    assert payload["isin_concentration_report"][0]["isin"] == "ISIN001"
    assert as_decimal(
        payload["isin_concentration_report"][0]["client_percentage"]
    ) == Decimal("100")


def test_analytics_endpoint_returns_200_with_empty_list_when_no_analytics(
    api_client,
) -> None:
    client, _session_factory = api_client

    response = client.get("/analytics")

    assert response.status_code == 200
    assert response.json() == {
        "top_traded_isins": [],
        "average_holding_time_per_client": [],
        "most_volatile_client": None,
        "isin_concentration_report": [],
    }
