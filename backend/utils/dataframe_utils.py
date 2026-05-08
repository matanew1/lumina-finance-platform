from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd


def normalize_column_name(column: object, aliases: Mapping[str, str] | None = None) -> str:
    compact_name = compact_key(column)
    if aliases and compact_name in aliases:
        return aliases[compact_name]
    return str(column)


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
