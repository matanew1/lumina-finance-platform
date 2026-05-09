from decimal import Decimal

import pandas as pd

from backend.app.api.schemas.transactions import TransactionUploadError
from backend.app.services.shared.dataframe_utils import (
    compact_key,
    is_blank_cell,
    normalize_string_cell,
    parse_decimal_cell,
)
from backend.app.services.transactions.schemas import TransactionIngested
from backend.app.utils.exceptions import ValidationAppError

REQUIRED_COLUMNS = (
    "client_id",
    "transaction_id",
    "isin",
    "action",
    "quantity",
    "price",
    "timestamp",
)
COLUMN_ALIASES = {
    "clientid": "client_id",
    "transactionid": "transaction_id",
    "isin": "isin",
    "action": "action",
    "quantity": "quantity",
    "price": "price",
    "timestamp": "timestamp",
}
STRING_COLUMNS = ("client_id", "transaction_id", "isin", "action")
VALID_ACTIONS = {"buy", "sell"}


def normalize_transaction_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.rename(
        columns=lambda column: COLUMN_ALIASES.get(compact_key(column), str(column))
    ).copy()
    missing = [column for column in REQUIRED_COLUMNS if column not in normalized.columns]
    if missing:
        raise ValidationAppError(
            f"Missing required transaction columns: {', '.join(missing)}."
        )

    normalized = normalized.loc[:, list(REQUIRED_COLUMNS)]
    for column in STRING_COLUMNS:
        normalized[column] = normalized[column].apply(normalize_string_cell)

    normalized["action"] = normalized["action"].apply(
        lambda value: value.lower() if isinstance(value, str) else value
    )
    normalized["quantity"] = normalized["quantity"].apply(parse_decimal_cell)
    normalized["price"] = normalized["price"].apply(parse_decimal_cell)
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce")

    return normalized


def validate_transaction_dataframe(
    dataframe: pd.DataFrame,
) -> list[TransactionUploadError]:
    errors: list[TransactionUploadError] = []

    for index, row in dataframe.iterrows():
        row_number = int(index) + 2

        for column in ("client_id", "transaction_id", "isin"):
            if is_blank_cell(row[column]):
                errors.append(
                    _validation_error(
                        row_number,
                        column,
                        "Value is required.",
                        row[column],
                    )
                )

        if is_blank_cell(row["action"]) or row["action"] not in VALID_ACTIONS:
            errors.append(
                _validation_error(
                    row_number,
                    "action",
                    "Action must be Buy or Sell.",
                    row["action"],
                )
            )

        errors.extend(
            _validate_positive_decimal(
                row_number,
                "quantity",
                "Quantity",
                row["quantity"],
            )
        )
        errors.extend(
            _validate_positive_decimal(row_number, "price", "Price", row["price"])
        )

        if pd.isna(row["timestamp"]):
            errors.append(
                _validation_error(
                    row_number,
                    "timestamp",
                    "Timestamp must be a valid date/time.",
                    row["timestamp"],
                )
            )

    return errors


def transaction_records_from_dataframe(
    dataframe: pd.DataFrame,
) -> list[TransactionIngested]:
    return [
        TransactionIngested(
            client_id=row["client_id"],
            transaction_id=row["transaction_id"],
            isin=row["isin"],
            action=row["action"],
            quantity=row["quantity"],
            price=row["price"],
            timestamp=row["timestamp"].to_pydatetime(),
        )
        for row in dataframe.to_dict("records")
    ]


def _validate_positive_decimal(
    row_number: int,
    field: str,
    display_name: str,
    value: Decimal | None,
) -> list[TransactionUploadError]:
    if value is None:
        return [
            _validation_error(
                row_number,
                field,
                f"{display_name} must be a number.",
                value,
            )
        ]
    if value <= 0:
        return [
            _validation_error(
                row_number,
                field,
                f"{display_name} must be greater than 0.",
                value,
            )
        ]
    return []


def _validation_error(
    row_number: int | None,
    field: str,
    message: str,
    value: object,
) -> TransactionUploadError:
    return TransactionUploadError(
        row_number=row_number,
        field=field,
        message=message,
        value=None if pd.isna(value) else str(value),
    )
