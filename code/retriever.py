"""
retriever.py — TF-IDF retriever (stdlib only, no sklearn).

Loads the scraped support corpus from data/ and supports retrieving
the most relevant documents for a given query, optionally filtered
or prioritized by company.
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent.parent / "data"

COMPANY_TO_FOLDER = {
    "hackerrank": "hackerrank",
    "claude": "claude",
    "visa": "visa",
}

STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "this", "that", "these",
    "those", "i", "you", "he", "she", "it", "we", "they", "my", "your",
    "his", "her", "its", "our", "their", "what", "which", "who", "how",
    "when", "where", "why", "not", "no", "yes", "so", "if", "then",
}


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())
    return [t for t in tokens if t not in STOP_WORDS]


def _tf(tokens: list[str]) -> dict[str, float]:
    counts: dict[str, int] = defaultdict(int)
    for t in tokens:
        counts[t] += 1
    total = max(len(tokens), 1)
    return {term: count / total for term, count in counts.items()}


class Document:
    def __init__(self, url: str, title: str, content: str, company: str):
        self.url = url
        self.title = title
        self.content = content
        self.company = company
        self.tokens = _tokenize(f"{title} {content}")
        self.tf = _tf(self.tokens)


def load_corpus() -> list[Document]:
    docs: list[Document] = []
    for company, folder in COMPANY_TO_FOLDER.items():
        folder_path = DATA_DIR / folder
        if not folder_path.exists():
            continue
        for json_file in folder_path.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                doc = Document(
                    url=data.get("url", ""),
                    title=data.get("title", ""),
                    content=data.get("content", ""),
                    company=company,
                )
                if len(doc.tokens) > 5:
                    docs.append(doc)
            except Exception:
                pass
    return docs


class TFIDFRetriever:
    def __init__(self) -> None:
        self.docs: list[Document] = []
        self.idf: dict[str, float] = {}

    def build(self, corpus: list[Document]) -> None:
        self.docs = corpus
        N = len(corpus)
        if N == 0:
            return
        df: dict[str, int] = defaultdict(int)
        for doc in corpus:
            for term in set(doc.tokens):
                df[term] += 1
        self.idf = {term: math.log((N + 1) / (freq + 1)) + 1.0 for term, freq in df.items()}

    def _score(self, query_tokens: list[str], doc: Document) -> float:
        score = 0.0
        for term in query_tokens:
            if term in self.idf and term in doc.tf:
                score += doc.tf[term] * self.idf[term]
        return score

    def retrieve(
        self,
        query: str,
        company: str | None = None,
        top_k: int = 4,
    ) -> list[Document]:
        if not self.docs:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return self.docs[:top_k]

        company_norm = company.lower().strip() if company else None

        primary: list[tuple[float, Document]] = []
        secondary: list[tuple[float, Document]] = []

        for doc in self.docs:
            score = self._score(query_tokens, doc)
            if company_norm and doc.company == company_norm:
                primary.append((score, doc))
            else:
                secondary.append((score, doc))

        primary.sort(key=lambda x: x[0], reverse=True)
        secondary.sort(key=lambda x: x[0], reverse=True)

        results: list[Document] = []
        for _, doc in primary:
            results.append(doc)
            if len(results) >= top_k:
                break

        if len(results) < top_k:
            for _, doc in secondary:
                results.append(doc)
                if len(results) >= top_k:
                    break

        return results


def get_context_for_ticket(
    issue: str,
    subject: str,
    company: str | None,
    retriever: TFIDFRetriever,
    top_k: int = 4,
) -> str:
    query = f"{subject} {issue}".strip()
    docs = retriever.retrieve(query, company=company, top_k=top_k)
    if not docs:
        return "No relevant corpus documents found."

    parts: list[str] = []
    for i, doc in enumerate(docs, 1):
        snippet = doc.content[:1500]
        parts.append(
            f"--- Document {i} [{doc.company.upper()}] ---\n"
            f"Title: {doc.title}\n"
            f"URL: {doc.url}\n"
            f"Content:\n{snippet}\n"
        )
    return "\n".join(parts)
