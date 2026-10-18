import pytest

from app import workflow


def test_diagnosis_route_records_trace_and_diagnosis(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

    state = workflow.graph.invoke({"question": "Why is my pod OOMKilled and restarting?"})

    assert state["intent"] == "diagnose"
    assert state["diagnosis"].startswith("Diagnostic evidence retrieved")
    assert state["trace_steps"] == [
        "router:diagnose", "diagnose:retrieved_evidence", "answer:completed"
    ]


def test_knowledge_route_records_trace(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

    state = workflow.graph.invoke({"question": "What is a Kubernetes container image?"})

    assert state["intent"] == "knowledge"
    assert state["trace_steps"] == [
        "router:knowledge", "knowledge:retrieved_sources", "answer:completed"
    ]


def test_no_matching_documents_returns_visible_failure(monkeypatch):
    monkeypatch.setattr(workflow, "search_docs", lambda _question: [])

    state = workflow.graph.invoke({"question": "Explain sourdough bread"})

    assert state["answer"] == "No relevant documentation found. Please provide more details."
    assert state["trace_steps"][-1] == "answer:no_sources"


def test_retrieval_error_is_not_hidden(monkeypatch):
    def unavailable(_question):
        raise RuntimeError("corpus unavailable")

    monkeypatch.setattr(workflow, "search_docs", unavailable)

    with pytest.raises(RuntimeError, match="corpus unavailable"):
        workflow.graph.invoke({"question": "What is a deployment?"})
