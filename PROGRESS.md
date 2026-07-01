# Progress

Running log of what is built, phase by phase. Newest entries at the top of each phase.

## Phase 5 - Self-reflection / critic loop (done)

- **Critic node** (`agent/nodes.py` `make_critic`): an LLM-as-a-judge reads question + context +
  draft and returns `VERDICT: SUFFICIENT|INSUFFICIENT` + reason (`_parse_verdict`, fails OPEN on
  unparseable output so it cannot trap the loop).
- **Conditional loop edge** (`graph.py`): `drafter -> critic`, then a conditional edge routes an
  insufficient answer back to `planner`; a sufficient answer (or an exhausted budget) goes to
  `output_guard`. The planner re-plans using the critic's feedback on a retry.
- **Bounded**: `retries` (critic-rejection count) lives in state; `route_after_critic` stops once
  it exceeds `max_retries` (default 1, a setting). Cannot loop forever.
- **State/REST**: added `retries`, `critic_sufficient`, `critic_feedback`; `/ask` returns
  `retries`.
- **Tests:** 26 total; added critic happy-path (no loop, retries 0) + loop-bound (planner/critic
  run exactly twice at max_retries=1, then terminate).
- **Verified live (Claude):** critic runs and judges SUFFICIENT on a covered question (no loop,
  grounded); it also accepted an honest "not covered" as sufficient (a lenient-decline policy
  choice, not a bug). Loop + bound proven deterministically in tests.

## Phase 4 - Guardrails (done)

- **`groundwork_api/guardrails/`** (pure, deterministic, no LLM):
  - `pii.py` - regex detect/redact for EMAIL, SSN, PHONE, CREDIT_CARD.
  - `injection.py` - pattern screen for override-instructions / reveal-prompt / role-hijack /
    jailbreak.
  - `checks.py` - `check_input` (redact PII, block injection) + `check_output` (grounding by
    citation match, PII-leak redaction).
- **Graph wiring** (`agent/guards.py`, `graph.py`): `input_guard` and `output_guard` nodes; a
  **conditional edge** routes a blocked (injection) request straight to END with a refusal, before
  any LLM call. New state fields: `blocked`, `grounded`, `flags` (reducer-accumulated).
- **REST**: `/ask` now returns `blocked`, `grounded`, `flags`.
- **Tests:** 25 total (was 7); +18 for guardrails (PII, injection, grounding units + agent
  integration: injection blocked pre-LLM, PII redacted then answered, uncited answer flagged
  ungrounded).
- **Verified live (Claude):** injection request refused with ONLY `input_guard` running (zero LLM
  cost, conditional edge worked); an email in the question was redacted to `[REDACTED_EMAIL]`
  before reaching the model (the model even noted the redaction) and the answer came back grounded.

## Phase 3 - Agent v1 (LangGraph) (done)

- **`apps/api`** (uv package, path-depends on `retrieval`):
  - `agent/state.py` - `AgentState` TypedDict; `notes` uses an `add` reducer (accumulates) while
    other keys overwrite. Reducer is a teaching device now, the mechanism the Phase 5 critic loop
    will use.
  - `agent/nodes.py` - planner (LLM rewrites question -> search query), retriever (hybrid search),
    drafter (grounded answer + deterministic citations). Factory-built, dependency-injected.
  - `agent/graph.py` - linear StateGraph: START -> planner -> retriever -> drafter -> END.
  - `agent/prompts.py` - planner/drafter system prompts + the RAG augment prompt.
  - `llm.py` - provider factory (claude | openai | ollama); nodes call `.invoke().content`, never
    know the provider (the seam the Phase 10 eval harness uses).
  - `service.py` - `AgentService` (answer/stream); single construction path for app + CLI.
  - `app.py` - FastAPI `POST /ask` + `/health`; OpenAPI 3.1 schema; service injected for test
    override.
  - `cli.py` - `groundwork-api ask [--trace] | serve`. `--trace` streams per-node state.
  - `tests/` - 7 tests (graph w/ fake LLM, citations, notes-reducer, stream order, endpoint),
    no network.
- **`ingestion` config (additive):** LLM settings (default_provider, anthropic/openai/ollama
  models + keys). `.env.example`: `DEFAULT_PROVIDER`, default Anthropic model = sonnet-4-6 (cheaper
  than opus for an agent loop).
- **Verified:** 7/7 tests pass; OpenAPI 3.1 generates with `/ask`. **Live-verified end to end on
  two providers** with grounded, cited answers that correctly refused to invent the k=60 origin
  absent from context:
  - **Claude (sonnet-4-6):** works.
  - **Ollama Cloud (`gpt-oss:120b-cloud`, free tier):** works, via the signed-in local daemon
    proxying to Ollama's servers (no local GPU). `glm-5.2:cloud` returns 403 (paid subscription).
  Verified through BOTH surfaces: the `ask` CLI and the real `POST /ask` HTTP endpoint (TestClient
  hitting the live agent, no fakes) returned 200 with grounded, cited answers on each provider.
- **Two bugs caught live and fixed:**
  1. sonnet-4-6 rejects `temperature` (`400 deprecated`); no longer passed to `ChatAnthropic`.
  2. Windows `cp1252` console crashed on a model answer containing U+202F; `cli.main` now
     reconfigures stdout/stderr to UTF-8.
- **Ollama auth learning (in `.env.example`):** ollama.com/settings/keys holds your daemon's
  ed25519 PUBLIC key (register it via `ollama signin`), not a bearer token. Cloud path = signed-in
  daemon at localhost + a `:cloud` model + blank `OLLAMA_API_KEY`.
- **Learner scaffolding:** teaching-grade comments throughout the agent; `docs/agents.md`
  walkthrough ending in a reproducible trace; `--trace` mode.

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
| 3 | Agent v1 (LangGraph) | done |
| 4 | Guardrails | done |
| 5 | Self-reflection + critic | done |
| 6 | MCP | not started |
| 7 | Rust rerank service | not started |
| 8 | HITL UI | not started |
| 9 | Observability | not started |
| 10 | Eval harness | not started |
| 11 | Infra + docs | not started |
