"""Reranking seam.

Fusion gives an approximate order. A cross-encoder reranker reads each query-document pair
together and scores relevance directly, which is more accurate but too slow to run over the
whole corpus, so it runs only over the fused candidate set (see packages/kb/hybrid-search.md).

That cross-encoder is the Rust service built in Phase 7. For now the seam exists with a no-op
passthrough so the rest of the pipeline is wired against the `Reranker` interface and Phase 7
is a drop-in swap, not a rewrite.
"""

from __future__ import annotations

from typing import Protocol


class Reranker(Protocol):
    def rerank(self, query: str, candidates: list[tuple[str, str]], top_k: int) -> list[str]:
        """Given (id, text) candidates, return up to top_k ids in reranked order."""
        ...


class NoOpReranker:
    """Passthrough: keep the fused order, just truncate to top_k. Replaced by the Rust
    cross-encoder service in Phase 7."""

    name = "noop"

    def rerank(self, query: str, candidates: list[tuple[str, str]], top_k: int) -> list[str]:
        return [cid for cid, _ in candidates[:top_k]]
