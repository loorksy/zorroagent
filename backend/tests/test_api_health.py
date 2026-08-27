from fastapi.testclient import TestClient

from app.main import app


def test_health_never_fakes_live_prices():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["mcp"] is False
    assert "personal analysis" in body["disclaimer"].lower()
    assert body["feeds"]["oanda"]["status"] in {"connected", "disconnected", "degraded", "diverged"}


def test_models_catalog_is_anthropic_only():
    client = TestClient(app)
    r = client.get("/api/models")
    ids = [m["id"] for m in r.json()["models"]]
    assert ids == [
        "claude-fable-5",
        "claude-opus-5",
        "claude-opus-4-8",
        "claude-sonnet-5",
        "claude-opus-4-7",
    ]
    assert "gpt" not in "".join(ids)
    assert "gemini" not in "".join(ids)
    assert "haiku" not in "".join(ids)


def test_routes_document_no_mcp():
    client = TestClient(app)
    r = client.get("/api/routes")
    assert r.json()["mcp"] is False
