"""Small BM25 retriever over the locally cached Kubernetes documentation."""

import json
import math
import re
from collections import Counter
from pathlib import Path

DEFAULT_CORPUS = Path(__file__).resolve().parents[1] / "data" / "docs.json"
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "do", "does", "for", "from",
    "how", "i", "in", "is", "it", "my", "of", "on", "or", "the", "to", "was", "what",
    "when", "where", "why", "with", "your",
}


def tokenize(text: str) -> list[str]:
    """Convert text into lowercase words while keeping repeated words for BM25."""
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS]


def format_citations(passages: list[dict]) -> str:
    """Return source URLs that can be appended to an answer without inventing links."""
    urls = list(dict.fromkeys(passage["url"] for passage in passages))
    return "\n\nSources:\n" + "\n".join(f"- {url}" for url in urls)


def search_docs(question: str, limit: int = 3, path: Path = DEFAULT_CORPUS) -> list[dict]:
    """Return BM25-ranked passages from a local corpus without network access."""
    documents = json.loads(Path(path).read_text(encoding="utf-8"))
    query_words = tokenize(question)
    if not query_words or not documents:
        return []

    tokens_by_document = [tokenize(f"{doc['title']} {doc['text']}") for doc in documents]
    average_length = sum(len(tokens) for tokens in tokens_by_document) / len(tokens_by_document)
    document_frequency = Counter(
        word for tokens in tokens_by_document for word in set(tokens)
    )
    total_documents = len(documents)
    ranked: list[tuple[float, dict]] = []
    for document, tokens in zip(documents, tokens_by_document):
        frequencies = Counter(tokens)
        score = 0.0
        for word in query_words:
            frequency = frequencies[word]
            if not frequency:
                continue
            inverse_frequency = math.log(
                1 + (total_documents - document_frequency[word] + 0.5)
                / (document_frequency[word] + 0.5)
            )
            length_normalizer = 1.5 * (1 - 0.75 + 0.75 * len(tokens) / average_length)
            score += inverse_frequency * frequency * (1.5 + 1) / (frequency + length_normalizer)
        if score:
            ranked.append((score, document))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return [{**doc, "score": score} for score, doc in ranked[:limit]]
