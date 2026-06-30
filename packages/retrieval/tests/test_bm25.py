"""BM25 index + tokenizer tests. No network."""

from __future__ import annotations

from ingestion.store import Record

from retrieval.bm25 import BM25Index, tokenize
from retrieval.rerank import NoOpReranker


def test_tokenize_lowercases_and_splits_on_nonalnum():
    assert tokenize("Reciprocal-Rank Fusion (RRF)!") == ["reciprocal", "rank", "fusion", "rrf"]


def _corpus() -> list[Record]:
    return [
        Record(id="d1", text="reciprocal rank fusion merges ranked lists", metadata={}),
        Record(id="d2", text="cosine similarity compares embedding vectors", metadata={}),
        Record(id="d3", text="bm25 is a sparse keyword scoring function", metadata={}),
    ]


def test_bm25_ranks_exact_term_match_first():
    idx = BM25Index(_corpus())
    ranked = idx.search("bm25 keyword", n=3)
    assert ranked[0][0] == "d3"


def test_bm25_returns_at_most_n():
    idx = BM25Index(_corpus())
    assert len(idx.search("fusion", n=2)) <= 2


def test_bm25_empty_corpus_is_safe():
    idx = BM25Index([])
    assert idx.search("anything", n=5) == []


def test_noop_reranker_preserves_order_and_truncates():
    candidates = [("a", "ta"), ("b", "tb"), ("c", "tc")]
    assert NoOpReranker().rerank("q", candidates, top_k=2) == ["a", "b"]
