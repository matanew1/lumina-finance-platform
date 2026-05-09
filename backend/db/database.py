from __future__ import annotations

import logging
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.db.models.base import Base
from backend.utils.config.settings import settings

logger = logging.getLogger(__name__)


class Database:
    _instance: Database | None = None

    def __new__(cls) -> Database:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        engine_kwargs: dict[str, object] = {"pool_pre_ping": True, "future": True}
        if settings.database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}

        self.engine = create_engine(
            settings.database_url,
            **engine_kwargs,
        )
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )
        self._schema_initialized = False
        self._initialized = True
        logger.debug("Database service initialized.")

    def get_session(self) -> Generator[Session, None, None]:
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()

    def init_schema(self) -> None:
        if self._schema_initialized:
            logger.debug("Database schema initialization skipped; already initialized.")
            return

        import backend.db.models  # noqa: F401

        Base.metadata.create_all(bind=self.engine)
        self._schema_initialized = True
        logger.info("Database schema initialized.")


db_service = Database()


def get_db() -> Generator[Session, None, None]:
    yield from db_service.get_session()
