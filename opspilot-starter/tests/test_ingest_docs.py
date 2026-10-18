from scripts.ingest_docs import URLS, extract_page, fetch_html, ingest


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None


class FakeSession:
    def __init__(self, html: str):
        self.html = html
        self.urls: list[str] = []

    def get(self, url: str, **_kwargs) -> FakeResponse:
        self.urls.append(url)
        return FakeResponse(self.html)


def test_ingest_caches_three_official_pages_and_writes_required_metadata(tmp_path):
    html = "<html><title>Official Kubernetes guide</title><main>" + ("Kubernetes memory limit guidance. " * 30) + "</main></html>"
    session = FakeSession(html)
    output = tmp_path / "docs.json"
    cache_dir = tmp_path / "cache"

    documents = ingest(session, output, cache_dir)

    assert session.urls == URLS
    assert output.exists()
    assert len(documents) >= 3
    assert {"title", "url", "retrieved_at", "chunk_id", "text"} <= documents[0].keys()
    assert {document["url"] for document in documents} == set(URLS)
    assert documents[0]["chunk_id"] == "page-1-chunk-1"
    assert list(cache_dir.glob("*.html"))


def test_extract_page_rejects_empty_or_garbled_content():
    try:
        extract_page("https://kubernetes.io/example", "<html><title>Error</title><main>!</main></html>")
    except RuntimeError as error:
        assert "Rejected empty or garbled" in str(error)
    else:
        raise AssertionError("garbled content should be rejected")


def test_fetch_html_reuses_cached_page_without_network(tmp_path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    cached_html = "<html><main>cached</main></html>"
    session = FakeSession("network should not be used")
    from scripts.ingest_docs import cache_path
    cache_path(URLS[0], cache_dir).write_text(cached_html, encoding="utf-8")

    html = fetch_html(URLS[0], session, cache_dir, refresh=False)

    assert html == cached_html
    assert session.urls == []
