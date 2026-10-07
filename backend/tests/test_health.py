from collections.abc import Callable, Iterator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db


class _OkSession:
    def execute(self, *_args: object, **_kwargs: object) -> int:
        return 1


class _BrokenSession:
    def execute(self, *_args: object, **_kwargs: object) -> None:
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))


def _override_with(session: object) -> Callable[[], Iterator[object]]:
    def _dependency() -> Iterator[object]:
        yield session

    return _dependency


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app"] == "AgentFlow AI"
    assert body["environment"] == "testing"


def test_request_id_is_generated(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert len(response.headers["X-Request-ID"]) == 32


def test_safe_request_id_is_echoed(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "abc-123"})
    assert response.headers["X-Request-ID"] == "abc-123"


def test_unsafe_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "bad id with spaces!"})
    assert response.headers["X-Request-ID"] != "bad id with spaces!"
    assert len(response.headers["X-Request-ID"]) == 32


def test_ready_when_database_ok(app: FastAPI, client: TestClient) -> None:
    app.dependency_overrides[get_db] = _override_with(_OkSession())
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok"}}


def test_ready_returns_503_when_database_down(app: FastAPI, client: TestClient) -> None:
    app.dependency_overrides[get_db] = _override_with(_BrokenSession())
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "checks": {"database": "unavailable"}}
    assert "connection refused" not in response.text  # internal details never leak


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert error["request_id"] == response.headers["X-Request-ID"]
