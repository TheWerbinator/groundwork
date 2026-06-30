"""Sparse keyword retrieval with BM25.

BM25 scores a document by how often the query's terms appear in it, weighted by how rare each
term is across the corpus, with term-frequency saturation and length normalization (see
packages/kb/hybrid-search.md). It nails exact terms and rare tokens that a dense embedding can
blur together, which is the half of hybrid search the vector index is weak at.

The index is built in memory from the same chunks the vector store holds. The corpus here is
small, so this is simple and fast; a larger deployment would persist a sparse index instead.
"""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from ingestion.store import Record

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase and split on non-alphanumeric runs. Deterministic and dependency-free, which
    keeps BM25 results reproducible and unit-testable."""
    return _TOKEN.findall(text.lower())


class BM25Index:
    def __init__(self, records: list[Record]) -> None:
        self._ids = [r.id for r in records]
        self._corpus_tokens = [tokenize(r.text) for r in records]
        # BM25Okapi requires a non-empty corpus; guard so an empty store fails clearly.
        self._bm25 = BM25Okapi(self._corpus_tokens) if records else None

    @classmethod
    def from_store(cls, store) -> "BM25Index":
        return cls(store.get_all())

    def search(self, query: str, n: int) -> list[tuple[str, float]]:
        """Return up to n (chunk_id, score) pairs ranked by BM25 score, highest first."""
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self._ids, scores), key=lambda p: p[1], reverse=True)
        return [(cid, float(score)) for cid, score in ranked[:n]]
