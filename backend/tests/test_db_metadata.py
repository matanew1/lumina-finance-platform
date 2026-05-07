from backend.models.base import Base
from backend import models  # noqa: F401


def test_database_metadata_contains_required_tables() -> None:
    tables = Base.metadata.tables

    assert {"transactions", "positions", "violations"}.issubset(tables.keys())


def test_transactions_columns_match_sample_workbook_shape() -> None:
    columns = Base.metadata.tables["transactions"].columns

    assert "client_id" in columns
    assert "transaction_id" in columns
    assert "isin" in columns
    assert "action" in columns
    assert "quantity" in columns
    assert "price" in columns
    assert "timestamp" in columns
