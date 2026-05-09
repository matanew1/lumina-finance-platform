from collections.abc import Callable, Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app

SessionFactory = Callable[[], Session]


@pytest.fixture
def api_client() -> Generator[tuple[TestClient, SessionFactory], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app), testing_session_local
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def as_decimal(value: object) -> Decimal:
    return Decimal(str(value))


def seed(session_factory: SessionFactory, *rows: object) -> None:
    with session_factory() as session:
        session.add_all(rows)
        session.commit()


def upload_csv(client: TestClient, csv: str):
    return client.post(
        "/upload-transactions",
        files={"file": ("transactions.csv", csv, "text/csv")},
    )


def valid_upload_csv() -> str:
    return "\n".join(
        [
            "client_id,transaction_id,isin,action,quantity,price,timestamp",
            "C001,T001,ISIN001,Buy,100,10.0,2024-01-01T10:00:00Z",
            "C002,T002,ISIN002,Buy,50,20.0,2024-01-01T09:00:00Z",
        ]
    )


def duplicate_transaction_upload_csv() -> str:
    return "\n".join(
        [
            "client_id,transaction_id,isin,action,quantity,price,timestamp",
            "C001,T001,ISIN001,Buy,100,10.0,2024-01-01T10:00:00Z",
            "C002,T001,ISIN002,Buy,50,20.0,2024-01-01T09:00:00Z",
        ]
    )
