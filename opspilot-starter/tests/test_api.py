from fastapi.testclient import TestClient
from app.api import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_returns_routing_trace(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

    response = TestClient(app).post(
        "/chat", json={"question": "Why is my pod OOMKilled and restarting?"}
    )

    assert response.status_code == 200
    assert response.json()["trace_steps"] == [
        "router:diagnose", "diagnose:retrieved_evidence", "answer:completed"
    ]


def test_approval_fails_without_code(tmp_path, monkeypatch):
    monkeypatch.setenv("OPSPILOT_DB", str(tmp_path / "api.db"))
    monkeypatch.setenv("DEMO_APPROVAL_CODE", "secret")
    client = TestClient(app)
    draft = client.post("/tickets/drafts", json={"title": "Pod crash", "summary": "Repeated restarts"})
    assert draft.status_code == 201
    draft_id = draft.json()["draft_id"]
    rejected = client.post(f"/tickets/drafts/{draft_id}/approve", json={"approval_code": "wrong"})
    assert rejected.status_code == 403
