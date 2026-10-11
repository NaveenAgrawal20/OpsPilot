"""Day 2: retrieve a SMALL, real public corpus from official Kubernetes pages.

Run: python scripts/ingest_docs.py
Review output before use; website structure and license may change.
"""

import json
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URLS = [
    "https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/",
    "https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/",
    "https://kubernetes.io/docs/concepts/containers/images/",
]
OUT = Path(__file__).resolve().parents[1] / "data" / "docs.json"


def chunks(text: str, size: int = 1000, overlap: int = 150) -> list[str]:
    """Split text into manageable overlapping excerpts."""
    return [text[pos:pos + size] for pos in range(0, len(text), size - overlap)]


def main():
    docs = []
    for url in URLS:
        response = requests.get(url, timeout=25, headers={"User-Agent": "OpsPilotDemo/0.1"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        main_content = soup.select_one("main") or soup.select_one("article")
        if main_content is None:
            raise RuntimeError(f"Could not locate article at {url}")
        for tag in main_content.select("nav, script, style, footer"):
            tag.decompose()
        title = soup.title.get_text(" ", strip=True) if soup.title else url
        content = main_content.get_text(" ", strip=True)
        for index, excerpt in enumerate(chunks(content)):
            if len(excerpt.strip()) < 120:
                continue
            docs.append({"title": f"{title} (part {index + 1})", "url": url,
                         "origin": "official_web_fetch", "text": excerpt})
    if not docs:
        raise RuntimeError("No documents fetched; keeping existing corpus")
    OUT.write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(docs)} passages to {OUT}")


if __name__ == "__main__":
    main()
