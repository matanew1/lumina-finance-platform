from decimal import Decimal, InvalidOperation

import pandas as pd


def compact_key(value: object) -> str:
    return "".join(char for char in str(value).strip().lower() if char.isalnum())


def normalize_string_cell(value: object) -> str | None:
    '''
    Normalize a cell value by stripping whitespace and converting to lowercase. If the value is blank or NaN, return None.
    - Parameters:
        - value: object - The value to normalize.
    - Returns:
        - str | None: The normalized string value, or None if the value is blank or NaN.
    '''
    if pd.isna(value):
        return None
    normalized = str(value).strip()
    return normalized or None


def is_blank_cell(value: object) -> bool:
    '''
    Check if a cell value is blank, which includes None, NaN, or strings that are empty or contain only whitespace.
    - Parameters:
        - value: object - The value to check.
    - Returns:
        - bool: True if the value is considered blank, False otherwise.
    '''
    return (
        value is None
        or pd.isna(value)
        or (isinstance(value, str) and not value.strip())
    )


def parse_decimal_cell(value: object) -> Decimal | None:
    '''
    Parse a cell value into a Decimal. If the value is blank, NaN, or cannot be parsed as a valid Decimal, return None.
    - Parameters:
        - value: object - The value to parse.
    - Returns:
        - Decimal | None: The parsed Decimal value, or None if the value is blank, NaN, or invalid.
    '''
    if is_blank_cell(value) or pd.isna(value):
        return None

    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None
