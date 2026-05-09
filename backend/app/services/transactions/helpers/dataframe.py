from decimal import Decimal

import pandas as pd

from backend.app.schemas.transactions import TransactionUploadError
from backend.app.utils.dataframe import (
    compact_key,
    is_blank_cell,
    normalize_string_cell,
    parse_decimal_cell,
)
from backend.app.schemas.transactions import TransactionIngested
from backend.app.utils.constants import (
    COLUMN_ALIASES,
    REQUIRED_COLUMNS,
    STRING_COLUMNS,
    VALID_ACTIONS,
)
from backend.app.utils.exceptions import ValidationAppError


def normalize_transaction_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    '''
    Normalizes the transaction DataFrame by standardizing column names, ensuring required columns are present, and converting data types.
    - Parameters:
        - dataframe: pd.DataFrame - The raw DataFrame containing transaction data.
    - Returns:
        - pd.DataFrame: A normalized DataFrame with standardized column names and data types.
    - Raises:
        - ValidationAppError: If any required columns are missing from the DataFrame.
    '''

    # Standardize column names by applying aliases and compacting keys, then create a copy of the DataFrame
    normalized = dataframe.rename(
        columns=lambda column: COLUMN_ALIASES.get(compact_key(column), str(column))
    ).copy()

    # Check for missing required columns and raise a validation error if any are missing
    missing = [column for column in REQUIRED_COLUMNS if column not in normalized.columns]
    if missing:
        raise ValidationAppError(
            f"Missing required transaction columns: {', '.join(missing)}."
        )

    # Reorder the DataFrame to ensure required columns are in a consistent order, and normalize string columns and convert data types for quantity, price, and timestamp
    normalized = normalized.loc[:, list(REQUIRED_COLUMNS)]
    for column in STRING_COLUMNS:
        # Normalize string columns by stripping whitespace and converting to lowercase
        normalized[column] = normalized[column].apply(normalize_string_cell)

    # Convert the "action" column to lowercase
    normalized["action"] = normalized["action"].apply(
        lambda value: value.lower() if isinstance(value, str) else value
    )
    # Convert "quantity" column to Decimal, and handle any parsing errors gracefully
    normalized["quantity"] = normalized["quantity"].apply(parse_decimal_cell)

    # Convert "price" column to Decimal, and handle any parsing errors gracefully
    normalized["price"] = normalized["price"].apply(parse_decimal_cell)

    # Convert "timestamp" column to datetime, and handle any parsing errors gracefully by coercing invalid values to NaT
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce")

    return normalized


def validate_transaction_dataframe(
    dataframe: pd.DataFrame,
) -> list[TransactionUploadError]:
    '''
    Validates the transaction DataFrame by checking for required fields, ensuring valid actions, and verifying that quantity and price are positive numbers.
    - Parameters:
        - dataframe: pd.DataFrame - The normalized DataFrame containing transaction data.
    - Returns:
        - list[TransactionUploadError]: A list of validation errors found in the DataFrame, including row numbers, field names, error messages, and the invalid values.
    '''
    # Initialize an empty list to collect validation errors
    errors: list[TransactionUploadError] = []

    for index, row in dataframe.iterrows():
        # Calculate the row number for error reporting (adding 2 to account for header and 0-based index)
        row_number = int(index) + 2

        # Check for required fields and validate that the "action" field contains a valid value, while also validating that "quantity" and "price" are positive numbers
        for column in ("client_id", "transaction_id", "isin"):
            # Validate that required string fields are not blank
            if is_blank_cell(row[column]):
                errors.append(
                    _validation_error(
                        row_number,
                        column,
                        "Value is required.",
                        row[column],
                    )
                )

        # Validate that the "action" field contains a valid value (either "buy" or "sell")
        if is_blank_cell(row["action"]) or row["action"] not in VALID_ACTIONS:
            errors.append(
                _validation_error(
                    row_number,
                    "action",
                    "Action must be Buy or Sell.",
                    row["action"],
                )
            )

        # Validate that "quantity" and "price" are positive numbers
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

        # Validate that the "timestamp" field is a valid date/time value (not NaT)
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
    '''
    Validates that a given value is a positive Decimal number, and returns a list of validation errors if the value is invalid.
    - Parameters:
        - row_number: int - The row number in the DataFrame for error reporting.
        - field: str - The name of the field being validated.
        - display_name: str - A user-friendly name for the field to be used in error messages.
        - value: Decimal | None - The value to be validated, which can be a Decimal number or None.
    - Returns:
        - list[TransactionUploadError]: A list containing a TransactionUploadError if the value is invalid (either None or not greater than 0), or an empty list if the value is valid.
    '''
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
