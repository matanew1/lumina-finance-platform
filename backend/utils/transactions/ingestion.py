from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import UploadFile

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


async def read_transaction_file(file: UploadFile) -> pd.DataFrame:
    contents = await read_upload_bytes(
        file,
        allowed_extensions=(".csv", ".xlsx"),
        unsupported_message="Only .csv or .xlsx transaction files are supported.",
        empty_message="Uploaded transaction file is empty.",
    )

    try:
        if Path(file.filename or "").suffix.lower() == ".csv":
            dataframe = pd.read_csv(BytesIO(contents), dtype=str)
        else:
            dataframe = pd.read_excel(BytesIO(contents), engine="openpyxl", dtype=str)
    except Exception as exc:
        raise ValueError("Unable to parse uploaded transaction file.") from exc

    if dataframe.empty:
        raise ValueError("Uploaded transaction file contains no transaction rows.")

    return dataframe


async def read_upload_bytes(
    file: UploadFile,
    *,
    allowed_extensions: tuple[str, ...],
    unsupported_message: str,
    empty_message: str,
) -> bytes:
    if not has_allowed_extension(file.filename, allowed_extensions):
        raise ValueError(unsupported_message)

    contents = await file.read()
    if not contents:
        raise ValueError(empty_message)

    return contents


def has_allowed_extension(filename: str | None, allowed_extensions: tuple[str, ...]) -> bool:
    if not filename:
        return False
    return filename.lower().endswith(tuple(extension.lower() for extension in allowed_extensions))


def normalize_transaction_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    normalized = dataframe.rename(
        columns=lambda column: normalize_column_name(column, COLUMN_ALIASES)
    ).copy()
    missing = missing_columns(normalized, REQUIRED_COLUMNS)
    if missing:
        raise ValueError(f"Missing required transaction columns: {', '.join(missing)}.")

    normalized = normalized.loc[:, list(REQUIRED_COLUMNS)]
    for column in STRING_COLUMNS:
        normalized[column] = normalized[column].apply(normalize_string)

    normalized["action"] = normalized["action"].apply(
        lambda value: value.lower() if isinstance(value, str) else value
    )
    normalized["quantity"] = normalized["quantity"].apply(parse_decimal_cell)
    normalized["price"] = normalized["price"].apply(parse_decimal_cell)
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce")

    return normalized


def validate_transaction_dataframe(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    for index, row in dataframe.iterrows():
        row_number = int(index) + 2

        for column in ("client_id", "transaction_id", "isin"):
            if is_blank(row[column]):
                errors.append(validation_error(row_number, column, "Value is required.", row[column]))

        if is_blank(row["action"]) or row["action"] not in VALID_ACTIONS:
            errors.append(validation_error(row_number, "action", "Action must be Buy or Sell.", row["action"]))

        errors.extend(validate_positive_decimal(row_number, "quantity", "Quantity", row["quantity"]))
        errors.extend(validate_positive_decimal(row_number, "price", "Price", row["price"]))

        if pd.isna(row["timestamp"]):
            errors.append(
                validation_error(row_number, "timestamp", "Timestamp must be a valid date/time.", row["timestamp"])
            )

    return errors


def validate_positive_decimal(
    row_number: int,
    field: str,
    display_name: str,
    value: Decimal | None,
) -> list[dict[str, Any]]:
    if value is None:
        return [validation_error(row_number, field, f"{display_name} must be a number.", value)]
    if value <= 0:
        return [validation_error(row_number, field, f"{display_name} must be greater than 0.", value)]
    return []


def transaction_records_from_dataframe(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {
            "client_id": row["client_id"],
            "transaction_id": row["transaction_id"],
            "isin": row["isin"],
            "action": row["action"],
            "quantity": row["quantity"],
            "price": row["price"],
            "timestamp": row["timestamp"].to_pydatetime(),
        }
        for row in dataframe.to_dict("records")
    ]


def parse_decimal_cell(value: Any) -> Decimal | None:
    if is_blank(value) or pd.isna(value):
        return None

    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None


def normalize_column_name(column: object, aliases: Mapping[str, str]) -> str:
    compact_name = compact_key(column)
    return aliases.get(compact_name, str(column))


def compact_key(value: object) -> str:
    return "".join(char for char in str(value).strip().lower() if char.isalnum())


def missing_columns(dataframe: pd.DataFrame, required_columns: Sequence[str]) -> list[str]:
    return [column for column in required_columns if column not in dataframe.columns]


def normalize_string(value: object) -> str | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip()
    return normalized or None


def is_blank(value: object) -> bool:
    return value is None or pd.isna(value) or (isinstance(value, str) and not value.strip())


def validation_error(row_number: int | None, field: str, message: str, value: object) -> dict[str, Any]:
    return {
        "row_number": row_number,
        "field": field,
        "message": message,
        "value": None if pd.isna(value) else str(value),
    }
