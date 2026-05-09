import pandas as pd

from backend.utils.transactions.ingestion import (
    normalize_transaction_dataframe,
    validate_transaction_dataframe,
)


def test_transaction_upload_validation_reports_invalid_inputs() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "ClientId": "C001",
                "TransactionId": "T1001",
                "ISIN": "US1234567890",
                "Action": "Hold",
                "Quantity": 0,
                "Price": 0,
                "Timestamp": "not-a-date",
            }
        ]
    )

    errors = validate_transaction_dataframe(normalize_transaction_dataframe(dataframe))
    fields = {error["field"] for error in errors}

    assert {"action", "quantity", "price", "timestamp"}.issubset(fields)
