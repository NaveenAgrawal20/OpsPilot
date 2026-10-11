import pytest
from app.tickets import prepare_draft, approve_draft, create_approved_ticket, list_tickets


def test_approval_is_required_and_create_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("OPSPILOT_DB", str(tmp_path / "test.db"))
    draft = prepare_draft("K8s pod failing", "OOMKilled with memory pressure")
    with pytest.raises(PermissionError):
        create_approved_ticket(draft["draft_id"])
    approve_draft(draft["draft_id"])
    first = create_approved_ticket(draft["draft_id"])
    again = create_approved_ticket(draft["draft_id"])
    assert first["id"] == again["id"]
    assert len(list_tickets()) == 1
