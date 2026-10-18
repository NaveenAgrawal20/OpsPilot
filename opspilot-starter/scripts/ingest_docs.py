"""Day 2: retrieve a SMALL, real public corpus from official Kubernetes pages.

Run: python scripts/ingest_docs.py
Review output before use; website structure and license may change.
"""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URLS = [
    "https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/",
    "https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/",
    "https://kubernetes.io/docs/concepts/containers/images/",
]
OUT = Path(__file__).resolve().parents[1] / "data" / "docs.json"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"


def chunks(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    """Split text into manageable overlapping excerpts."""
    return [text[pos:pos + size] for pos in range(0, len(text), size - overlap)]


def cache_path(url: str, cache_dir: Path) -> Path:
    return cache_dir / f"{hashlib.sha256(url.encode()).hexdigest()}.html"


def fetch_html(url: str, session: requests.Session, cache_dir: Path, refresh: bool) -> str:
    """Use a local cache unless refresh was explicitly requested."""
    path = cache_path(url, cache_dir)
    if path.exists() and not refresh:
        return path.read_text(encoding="utf-8")
    response = session.get(url, timeout=25, headers={"User-Agent": "OpsPilotDemo/0.1"})
    response.raise_for_status()
    cache_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(response.text, encoding="utf-8")
    return response.text


def extract_page(url: str, html: str) -> tuple[str, str]:
    """Extract substantial readable article content and reject error/garbage pages."""
    soup = BeautifulSoup(html, "html.parser")
    main_content = soup.select_one("main") or soup.select_one("article")
    if main_content is None:
        raise RuntimeError(f"Could not locate article at {url}")
    for tag in main_content.select("nav, script, style, footer"):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    content = main_content.get_text(" ", strip=True)
    letters = sum(character.isalpha() for character in content)
    if not title or len(content) < 500 or letters < 300 or letters / len(content) < 0.45:
        raise RuntimeError(f"Rejected empty or garbled page at {url}")
    return title, content


def build_documents(url: str, title: str, content: str, retrieved_at: str, page_number: int) -> list[dict]:
    documents = []
    for index, excerpt in enumerate(chunks(content), start=1):
        if len(excerpt.strip()) < 120:
            continue
        documents.append({
            "title": title,
            "url": url,
            "retrieved_at": retrieved_at,
            "chunk_id": f"page-{page_number}-chunk-{index}",
            "text": excerpt,
        })
    if not documents:
        raise RuntimeError(f"No usable chunks at {url}")
    return documents


def ingest(session: requests.Session, output: Path, cache_dir: Path, refresh: bool = False) -> list[dict]:
    """Fetch exactly URLS, write the corpus only after every page succeeds."""
    docs = []
    retrieved_at = datetime.now(timezone.utc).isoformat()
    for page_number, url in enumerate(URLS, start=1):
        title, content = extract_page(url, fetch_html(url, session, cache_dir, refresh))
        docs.extend(build_documents(url, title, content, retrieved_at, page_number))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description="Cache and chunk three official Kubernetes pages.")
    parser.add_argument("--refresh", action="store_true", help="Download again instead of reusing cached HTML.")
    args = parser.parse_args()
    documents = ingest(requests.Session(), OUT, CACHE_DIR, refresh=args.refresh)
    print(f"Saved {len(documents)} passages to {OUT}")


if __name__ == "__main__":
    main()
