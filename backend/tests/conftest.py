import os
from collections.abc import Callable, Generator

os.environ.setdefault("AUTO_INIT_DB", "false")

import pytest
from fastapi.testclient import TestClient

from backend.db.database import get_db
from backend.main import app
from backend.tests.fakes import FakeUploadSession


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def fake_upload_session() -> FakeUploadSession:
    return FakeUploadSession()


@pytest.fixture
def override_db() -> Generator[Callable[[object], None], None, None]:
    def apply(fake_db: object) -> None:
        def override_get_db():
            yield fake_db

        app.dependency_overrides[get_db] = override_get_db

    try:
        yield apply
    finally:
        app.dependency_overrides.clear()
