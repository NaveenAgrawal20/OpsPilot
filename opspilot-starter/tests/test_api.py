from fastapi.testclient import TestClient
from app.api import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_approval_fails_without_code(tmp_path, monkeypatch):
    monkeypatch.setenv("OPSPILOT_DB", str(tmp_path / "api.db"))
    monkeypatch.setenv("DEMO_APPROVAL_CODE", "secret")
    client = TestClient(app)
    draft = client.post("/tickets/drafts", json={"title": "Pod crash", "summary": "Repeated restarts"})
    assert draft.status_code == 201
    draft_id = draft.json()["draft_id"]
    rejected = client.post(f"/tickets/drafts/{draft_id}/approve", json={"approval_code": "wrong"})
    assert rejected.status_code == 403
