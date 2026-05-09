from decimal import Decimal, InvalidOperation

import pandas as pd


def compact_key(value: object) -> str:
    return "".join(char for char in str(value).strip().lower() if char.isalnum())


def normalize_string_cell(value: object) -> str | None:
    if pd.isna(value):
        return None
    normalized = str(value).strip()
    return normalized or None


def is_blank_cell(value: object) -> bool:
    return (
        value is None
        or pd.isna(value)
        or (isinstance(value, str) and not value.strip())
    )


def parse_decimal_cell(value: object) -> Decimal | None:
    if is_blank_cell(value) or pd.isna(value):
        return None

    try:
        parsed = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return parsed if parsed.is_finite() else None
