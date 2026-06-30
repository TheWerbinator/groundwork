# packages/retrieval

The read path: hybrid search over the chunks [ingestion](../ingestion) loaded into Chroma.
Dense and sparse retrieval each rank the corpus, reciprocal-rank fusion merges the rankings,
and a reranker reorders the fused candidates (see
[packages/kb/hybrid-search.md](../kb/hybrid-search.md)).

- **Dense** - vector search over embeddings (`HybridRetriever.vector_search`).
- **Sparse** - BM25 over the same chunks, in-memory via `rank-bm25` (`bm25.py`).
- **Fusion** - Reciprocal Rank Fusion, `1/(k+rank)`, `k=60` (`fusion.py`).
- **Rerank** - `Reranker` protocol; `NoOpReranker` passthrough today, replaced by the Rust
  cross-encoder service in Phase 7 with no caller changes (`rerank.py`).

## Usage

```bash
cd packages/retrieval
uv sync
uv run retrieval search "how does reciprocal rank fusion work?"
uv run pytest               # RRF + BM25 unit tests (no network)
```

The `search` command prints the dense leg, the sparse leg, and the fused hybrid result side by
side, so the value of fusion over either method alone is visible. Requires the KB to be
ingested first (`uv run ingestion ingest` in `../ingestion`).

Retrieval knobs (`candidate_pool`, `top_k`, `rrf_k`) come from settings / `.env`.

**Learn how it works:** [docs/retrieval.md](../../docs/retrieval.md) is a guided walkthrough of
this code, including a worked RRF example.

**Built in:** Phase 2. The agent (Phase 3) and eval harness (Phase 10) consume this.
