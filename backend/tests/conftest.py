import os
from collections.abc import Iterator

# Tests use an isolated SQLite test database for fast, reliable local runs.
TEST_DB_PATH = "test_agentflow.db"
os.environ["DATABASE_URL"] = f"sqlite:///./{TEST_DB_PATH}"
os.environ["ENVIRONMENT"] = "testing"
os.environ["LOG_JSON"] = "false"
os.environ["LLM_PROVIDER"] = "mock"

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import app.models as _models  # noqa: F401, E402
from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_test_db() -> Iterator[None]:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass


@pytest.fixture
def app() -> Iterator[FastAPI]:
    application = create_app()
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
