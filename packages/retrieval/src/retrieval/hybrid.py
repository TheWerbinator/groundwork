"""Hybrid retriever: dense + sparse -> reciprocal-rank fusion -> rerank.

Ties the pieces together. The dense leg (vector search over embeddings) and the sparse leg
(BM25) each rank the corpus; RRF fuses the two rankings; the reranker reorders the fused
candidates and truncates to top_k. Each leg is exposed on its own so the teaching CLI can show
what fusion adds over either alone.
"""

from __future__ import annotations

from dataclasses import dataclass

from ingestion.config import Settings
from ingestion.embeddings import Embedder, build_embedder
from ingestion.store import ChromaStore, Record

from retrieval.bm25 import BM25Index
from retrieval.fusion import reciprocal_rank_fusion
from retrieval.rerank import NoOpReranker, Reranker


@dataclass
class HybridResult:
    id: str
    text: str
    metadata: dict
    score: float  # fused RRF score

    @property
    def source(self) -> str:
        return str(self.metadata.get("source", "?"))

    @property
    def heading(self) -> str:
        return str(self.metadata.get("heading", ""))


class HybridRetriever:
    def __init__(
        self,
        settings: Settings,
        embedder: Embedder | None = None,
        store: ChromaStore | None = None,
        reranker: Reranker | None = None,
    ) -> None:
        self._settings = settings
        self._embedder = embedder or build_embedder(settings)
        self._store = store or ChromaStore(settings)
        self._reranker = reranker or NoOpReranker()
        records = self._store.get_all()
        self._records: dict[str, Record] = {r.id: r for r in records}
        self._bm25 = BM25Index(records)

    def location(self, cid: str) -> str:
        """Human label for a chunk id: "source (heading)". Used by the teaching CLI to show
        each leg's hits."""
        record = self._records.get(cid)
        if record is None:
            return cid
        source = record.metadata.get("source", "?")
        heading = record.metadata.get("heading", "")
        return f"{source} ({heading})" if heading else str(source)

    def vector_search(self, query: str, n: int) -> list[str]:
        """Dense leg: ids ranked by ascending embedding distance (closest first)."""
        hits = self._store.query(self._embedder.embed_query(query), n_results=n)
        return [h.id for h in hits]

    def sparse_search(self, query: str, n: int) -> list[str]:
        """Sparse leg: ids ranked by BM25 score (highest first)."""
        return [cid for cid, _ in self._bm25.search(query, n)]

    def retrieve(
        self, query: str, top_k: int | None = None, candidate_pool: int | None = None
    ) -> list[HybridResult]:
        top_k = top_k or self._settings.top_k
        pool = candidate_pool or self._settings.candidate_pool

        dense = self.vector_search(query, pool)
        sparse = self.sparse_search(query, pool)
        fused = reciprocal_rank_fusion([dense, sparse], k=self._settings.rrf_k)

        score_by_id = dict(fused)
        candidates = [(cid, self._records[cid].text) for cid, _ in fused if cid in self._records]
        ordered_ids = self._reranker.rerank(query, candidates, top_k)

        results: list[HybridResult] = []
        for cid in ordered_ids:
            record = self._records[cid]
            results.append(
                HybridResult(
                    id=cid,
                    text=record.text,
                    metadata=record.metadata,
                    score=score_by_id.get(cid, 0.0),
                )
            )
        return results
