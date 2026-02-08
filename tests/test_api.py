import pytest
from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_index_serves_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "DebateArena" in resp.text


def test_debate_missing_key():
    """Should return an error event when no API key is available."""
    resp = client.post(
        "/api/debate",
        json={"topic": "test", "provider": "anthropic"},
    )
    # SSE stream, should contain error event
    assert resp.status_code == 200
    assert "error" in resp.text
