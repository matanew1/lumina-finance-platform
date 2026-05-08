from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd
from fastapi import UploadFile

from backend.utils.dataframe_utils import (
    is_blank,
    missing_columns,
    normalize_column_name,
    normalize_string,
    validation_error,
)
from backend.utils.upload_utils import read_excel_upload

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


async def read_transaction_excel(file: UploadFile) -> pd.DataFrame:
    return await read_excel_upload(
        file,
        unsupported_message="Only .xlsx transaction files are supported.",
        empty_message="Uploaded transaction file is empty.",
        parse_error_message="Unable to parse uploaded Excel file.",
        empty_dataframe_message="Uploaded transaction file contains no transaction rows.",
    )


def normalize_transaction_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:

    # Rename columns using aliases and check for missing required columns
    normalized = dataframe.rename(columns=lambda column: normalize_column_name(column, COLUMN_ALIASES)).copy()
    missing = missing_columns(normalized, REQUIRED_COLUMNS)
    if missing:
        missing_display = ", ".join(missing)
        raise ValueError(f"Missing required transaction columns: {missing_display}.")

    # Keep only required columns in a consistent order
    normalized = normalized.loc[:, list(REQUIRED_COLUMNS)]

    # Normalize string columns
    for column in STRING_COLUMNS:
        normalized[column] = normalized[column].apply(normalize_string)

    # Convert to appropriate data types and handle conversion errors
    normalized["action"] = normalized["action"].apply(
        lambda value: value.lower() if isinstance(value, str) else value
    )
    # coerce errors to NaN for numeric and datetime columns, which will be caught in validation
    normalized["quantity"] = pd.to_numeric(normalized["quantity"], errors="coerce")
    normalized["price"] = pd.to_numeric(normalized["price"], errors="coerce")
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce")

    return normalized


def validate_transaction_dataframe(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    for index, row in dataframe.iterrows():
        row_number = int(index) + 2 # add 2 to convert from 0-based index to 1-based Excel row number (accounting for header row)

        # Check for required columns
        for column in ("client_id", "transaction_id", "isin"):
            if is_blank(row[column]):
                errors.append(validation_error(row_number, column, "Value is required.", row[column]))

        # Check for valid action
        if is_blank(row["action"]) or row["action"] not in VALID_ACTIONS:
            errors.append(validation_error(row_number, "action", "Action must be Buy or Sell.", row["action"]))

        # Check for valid quantity and price 
        if pd.isna(row["quantity"]):
            errors.append(validation_error(row_number, "quantity", "Quantity must be a number.", row["quantity"]))
        elif row["quantity"] <= 0:
            errors.append(validation_error(row_number, "quantity", "Quantity must be greater than 0.", row["quantity"]))

        # Check for valid timestamp
        if pd.isna(row["price"]):
            errors.append(validation_error(row_number, "price", "Price must be a number.", row["price"]))
        elif row["price"] <= 0:
            errors.append(validation_error(row_number, "price", "Price must be greater than 0.", row["price"]))

        # Check for valid timestamp
        if pd.isna(row["timestamp"]):
            errors.append(validation_error(row_number, "timestamp", "Timestamp must be a valid date/time.", row["timestamp"]))

    return errors


def transaction_records_from_dataframe(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    for row in dataframe.to_dict("records"):
        records.append(
            {
                "client_id": row["client_id"],
                "transaction_id": row["transaction_id"],
                "isin": row["isin"],
                "action": row["action"],
                "quantity": Decimal(str(row["quantity"])),
                "price": Decimal(str(row["price"])),
                "timestamp": row["timestamp"].to_pydatetime(),
            }
        )

    return records
