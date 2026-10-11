"""Tiny, understandable lexical RAG retriever. Day 2 will improve it."""

import json
import re
from pathlib import Path

DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / "data" / "docs.json"


def tokenize(text: str) -> set[str]:
    """Convert a phrase into lowercase words for simple matching."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def search_docs(question: str, limit: int = 3, path: Path = DEFAULT_CORPUS) -> list[dict]:
    """Return the best-matching passages with real source URLs.

    This is a baseline lexical retriever, not semantic vector search.
    """
    documents = json.loads(Path(path).read_text(encoding="utf-8"))
    query_words = tokenize(question)
    ranked = []
    for doc in documents:
        overlap = query_words & tokenize(doc["text"] + " " + doc["title"])
        score = len(overlap)
        if score:
            ranked.append((score, doc))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [{**doc, "score": score} for score, doc in ranked[:limit]]
