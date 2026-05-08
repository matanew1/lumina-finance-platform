from backend.db.models.base import Base
from backend.db import models  # noqa: F401
from backend.db.session import build_engine_kwargs


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


def test_positions_columns_store_upload_time_fifo_results() -> None:
    columns = Base.metadata.tables["positions"].columns

    assert "client_id" in columns
    assert "isin" in columns
    assert "quantity" in columns
    assert "average_price" in columns
    assert "market_price" in columns
    assert "realized_pnl" in columns
    assert "unrealized_pnl" in columns


def test_sqlite_database_url_uses_thread_safe_fastapi_connect_args() -> None:
    kwargs = build_engine_kwargs("sqlite:///./lumina_finance.db")

    assert kwargs["connect_args"] == {"check_same_thread": False}


def test_postgresql_database_url_uses_default_connect_args() -> None:
    kwargs = build_engine_kwargs("postgresql+psycopg://postgres:postgres@localhost/lumina_finance")

    assert "connect_args" not in kwargs
