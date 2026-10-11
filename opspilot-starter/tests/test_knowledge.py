from app.knowledge import search_docs, tokenize


def test_tokens_are_case_insensitive():
    assert tokenize("Pod OOMKilled!") == {"pod", "oomkilled"}


def test_retrieval_returns_source_url():
    results = search_docs("OOMKilled memory limit")
    assert results
    assert "kubernetes.io" in results[0]["url"]
