from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path
from urllib.parse import unquote

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.utils.config import settings
from backend.app.db.base import Base

logger = logging.getLogger(__name__)


def _sqlite_path(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite"):
        return None

    if database_url in ("sqlite://", "sqlite:///:memory:"):
        return None

    if database_url.startswith("sqlite:///"):
        raw_path = unquote(database_url.removeprefix("sqlite:///"))
        if raw_path in ("", ":memory:"):
            return None
        path = Path(raw_path)
        return path if path.is_absolute() else Path.cwd() / path

    return None


def _engine_kwargs(database_url: str) -> dict[str, object]:
    kwargs: dict[str, object] = {"future": True}
    if database_url.startswith("sqlite"):
        sqlite_path = _sqlite_path(database_url)
        if sqlite_path is not None:
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        kwargs["connect_args"] = {"check_same_thread": False}
        return kwargs

    kwargs["pool_pre_ping"] = True
    return kwargs


engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
_schema_initialized = False


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_schema() -> None:
    global _schema_initialized

    if _schema_initialized:
        logger.debug("Database schema initialization skipped; already initialized.")
        return

    import backend.app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _schema_initialized = True
    logger.info("Database schema initialized.")
