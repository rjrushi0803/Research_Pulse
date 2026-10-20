from fastapi.testclient import TestClient

from app.main import create_app


def test_health_returns_ok_status() -> None:
    with TestClient(create_app(initialize_db=False)) as client:
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
    with TestClient(create_app(initialize_db=False)) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/health" in response.json()["paths"]
