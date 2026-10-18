import json

from app.knowledge import format_citations, search_docs, tokenize
from app.workflow import answer


def test_tokens_are_case_insensitive():
    assert tokenize("Pod OOMKilled!") == ["pod", "oomkilled"]


def test_tokens_drop_common_words_that_create_irrelevant_matches():
    assert tokenize("How do I restart my pod?") == ["restart", "pod"]


def test_retrieval_returns_source_url():
    results = search_docs("OOMKilled memory limit")
    assert results
    assert "kubernetes.io" in results[0]["url"]


def test_bm25_returns_relevant_chunk_and_rejects_irrelevant_question(tmp_path):
    corpus = tmp_path / "docs.json"
    corpus.write_text(json.dumps([
        {"title": "Memory limits", "url": "https://kubernetes.io/memory",
         "retrieved_at": "2026-10-18T00:00:00+00:00", "chunk_id": "memory-1",
         "text": "An OOMKilled container exceeded its memory limit."},
        {"title": "Images", "url": "https://kubernetes.io/images",
         "retrieved_at": "2026-10-18T00:00:00+00:00", "chunk_id": "images-1",
         "text": "ImagePullBackOff means the image cannot be downloaded."},
    ]), encoding="utf-8")

    results = search_docs("why was my container OOMKilled", path=corpus)

    assert results[0]["chunk_id"] == "memory-1"
    assert search_docs("how do I bake sourdough bread", path=corpus) == []
    assert "https://kubernetes.io/memory" in format_citations(results)


def test_retrieval_preview_includes_actual_source_urls(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    state = {
        "question": "What is a memory limit?",
        "sources": [{"title": "Memory limits", "url": "https://kubernetes.io/memory"}],
    }

    result = answer(state)["answer"]

    assert "LLM not configured" in result
    assert "https://kubernetes.io/memory" in result
