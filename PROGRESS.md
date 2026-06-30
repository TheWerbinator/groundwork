# Progress

Running log of what is built, phase by phase. Newest entries at the top of each phase.

## Teaching docs (learning path)

`docs/` is a guided learning path that explains how the code works (concept -> our code -> run
it -> exercises), distinct from the corpus (generic concepts) and DECISIONS.md (rationale).
Backfilled before Phase 3: [docs/ingestion.md](docs/ingestion.md),
[docs/retrieval.md](docs/retrieval.md) (with a worked RRF example). Phase 3 adds
`docs/agents.md` plus a `--trace` mode so a learner can watch the LangGraph state change at each
node. Linked from the root README and each package README.

## Phase 2 - Hybrid retrieval (done)

- **`packages/retrieval`** (uv package, path-depends on `ingestion`, reuses Settings /
  embedder / store):
  - `bm25.py` - in-memory BM25 (`rank-bm25`) over the same chunks the vector store holds;
    deterministic tokenizer.
  - `fusion.py` - `reciprocal_rank_fusion`, `1/(k+rank)`, k=60 (pure, testable).
  - `rerank.py` - `Reranker` protocol + `NoOpReranker` passthrough (Rust cross-encoder swaps
    in at Phase 7, no caller changes).
  - `hybrid.py` - `HybridRetriever`: dense + sparse legs -> RRF -> rerank -> top_k; each leg
    exposed for the teaching CLI.
  - `cli.py` - `retrieval search` prints dense vs sparse vs hybrid side by side.
  - `tests/` - 10 unit tests (RRF math, BM25 ranking, no network).
- **`ingestion` additions (additive):** `Retrieved.id`, `query` returns ids, new `Record` +
  `get_all()` (for the BM25 build); retrieval knobs in settings (`candidate_pool`, `top_k`,
  `rrf_k`).
- **Verified:** retrieval 10/10 + ingestion 6/6 pass; live comparison shows dense and sparse
  surfacing different chunks and RRF fusing them (e.g. an item appearing in both legs rises);
  exact-token query ("Streamable HTTP") confirms BM25's keyword strength.
- **Bug caught in verify:** a fusion unit test asserted the wrong RRF property (assumed
  consistent-2nd beats split-1st; the math is the opposite). Test corrected; code was right.

## Phase 1 - Corpus + ingestion (done)

- **Corpus:** 8 KB markdown docs under `packages/kb` (rag, chunking, embeddings,
  hybrid-search, langgraph-agents, mcp, evaluation, guardrails), each with frontmatter,
  cross-referenced, doubling as teaching content.
- **`packages/ingestion`** (uv package, src layout):
  - `chunking.py` - `MarkdownChunker` (heading-aware, stores heading path for citation) +
    `RecursiveChunker` fallback, behind a `Chunker` protocol.
  - `embeddings.py` - `FastEmbedEmbedder` (local bge-small, default) + `OpenAIEmbedder`
    (optional extra), behind an `Embedder` protocol; bge query instruction handled.
  - `store.py` - `ChromaStore`: local PersistentClient or `CHROMA_HOST` server, cosine space,
    deterministic-id upsert (idempotent re-ingest).
  - `config.py` - pydantic-settings from repo-root `.env`, local-first defaults.
  - `pipeline.py` + `cli.py` - `ingestion ingest` and `ingestion query`.
  - `tests/test_chunking.py` - 6 unit tests, no network.
- **Config:** `.env.example` reworked - fastembed default, `CHROMA_HOST` empty for local runs
  (compose api service sets it internally).
- **Verified:** 6/6 tests pass; ingest = 8 docs -> 40 chunks keyless; queries return the
  correct section with heading-path citation; re-ingest stays at 40 (no duplication).
- **Corpus audit (8 parallel research agents, web-verified):** fact-checked every doc and
  added per-section teaching-quality source links (sources ride along with the retrieved
  chunk). One real staleness bug fixed: MCP transport was "HTTP+SSE" (deprecated) -> now
  "stdio + Streamable HTTP" per spec 2025-11-25, plus client primitives + lifecycle added.
  Expansions: RAG augment step + reranking lever; chunking semantic/late + token-vs-char;
  embeddings MTEB + Matryoshka dims; langgraph reducers + checkpointing + AutoGen
  maintenance-mode caveat; eval retrieval-vs-answer metrics + named judge biases; guardrails
  lethal-trifecta + defense-in-depth limits. Re-ingest: 8 docs -> 60 chunks.

## Phase 0 - Bootstrap (done)

- Repo scaffolded: `apps/`, `packages/`, `eval/`, `infra/`, `docs/` directories.
- `.gitignore` with `.env*` guarded (`!.env.example`), polyglot rules (Python + Node + Rust).
- `.env.example` with placeholder keys.
- `infra/docker-compose.yml` skeleton (services declared, not yet wired).
- `README.md` index mapping each capability to its component.
- Planning docs: `PLAN.md`, `PROGRESS.md`, `DECISIONS.md`.

## Phase status

| # | Phase | Status |
|---|---|---|
| 0 | Bootstrap | done |
| 1 | Corpus + ingestion | done |
| 2 | Hybrid retrieval | done |
| 3 | Agent v1 (LangGraph) | not started |
| 4 | Guardrails | not started |
| 5 | Self-reflection + critic | not started |
| 6 | MCP | not started |
| 7 | Rust rerank service | not started |
| 8 | HITL UI | not started |
| 9 | Observability | not started |
| 10 | Eval harness | not started |
| 11 | Infra + docs | not started |
