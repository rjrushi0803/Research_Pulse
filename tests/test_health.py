"""Tests for the health endpoint."""

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok_status() -> None:
    """The health endpoint should return HTTP 200 and a stable response shape."""
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"] == "Research_Pulse"
    assert body["environment"] in {
        "development",
        "test",
        "staging",
        "production",
    }


def test_docs_endpoint_is_available() -> None:
    """FastAPI should expose its generated OpenAPI documentation."""
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/health" in response.json()["paths"]
