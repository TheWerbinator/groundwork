# Decisions

Architecture decisions and their rationale. Each entry: what was chosen, why, and the
alternatives rejected. Written so each is defensible in an interview.

## D0 - Scope and shape

- **Standalone repo, one cohesive product.** Separate from PromptForge to avoid coupling and
  keep the teaching narrative clean. Rejected: extending PromptForge (would blur product vs
  teaching and grow that repo too large).
- **Local-first, no live URL for v1.** The brief's cloud/k8s/multi-vendor list is expensive
  and not needed to *teach* the concepts. AWS + k8s ship as IaC + docs. Rejected: always-on
  AWS (ongoing cost, ops time not justified for a teaching artifact).
- **Self-referential corpus (AI-engineering knowledge base).** The KB is about the same tech
  the app uses, so demo output teaches the stack and doubles as study notes. Rejected:
  agency docs (privacy) and generic open dataset (no teaching synergy).

## D1 - Stack

- **Python / FastAPI backend, Next.js / TS frontend.** Matches existing stack preference
  (Python preferred; no Node backend, no Java). REST + OpenAPI gives a type-safe contract.
  Rejected: tRPC (needs a TS/Node backend).
- **LangGraph as the agent framework.** Explicit state-graph control over the
  planner/retriever/drafter/critic loop; good fit for teaching autonomous planning + self-
  reflection. AutoGen / CrewAI documented as alternatives in `docs/`.
- **Chroma for the vector store.** Zero-infra local default; hybrid (BM25 + vector + RRF)
  layered on top. Pinecone / Weaviate / Milvus documented as alternatives.
- **3-way model eval: Claude + OpenAI + Ollama.** Claude is the default strong model; GPT
  gives a second frontier vendor; Ollama covers the open-source / local angle and costs
  nothing. Makes the cost/latency/accuracy tradeoff real rather than fixture-based.
- **Rust rerank microservice (ONNX cross-encoder via `ort`).** The reranker is the genuine
  perf-sensitive hot path in RAG, so it best fits "high-performance inference service" and
  shows the polyglot boundary. Rejected: Rust cost/token gateway (simpler but not really
  inference).

## Phase 0 decisions

- _(none beyond D0/D1)_

## Phase 1 decisions

- **uv for Python tooling.** Single fast tool for deps, venv, and lockfile; current standard.
  Rejected: pip+requirements (no lockfile), Poetry (heavier, slower).
- **Local embeddings by default (fastembed `bge-small-en-v1.5`), OpenAI swappable.** Keeps the
  pipeline runnable with zero keys and zero spend, which fits local-first, and the swap is the
  concrete teaching point for "embeddings are interchangeable." OpenAI is an optional extra so
  the default install stays light. The bge query instruction is applied on queries only.
- **MarkdownChunker as the default strategy.** The corpus is Markdown, so heading-aware
  splitting keeps sections intact and yields a heading path for citation; oversized sections
  fall back to recursive character splitting. RecursiveChunker stays available as the
  structure-agnostic alternative. Sizes measured in characters to avoid a tokenizer dependency
  and keep chunking deterministic and unit-testable.
- **Compute embeddings explicitly, do not use Chroma's built-in embedding function.** Makes the
  embedding choice visible and swappable rather than hidden inside the store.
- **Deterministic chunk ids (`source:index`) with upsert.** Re-running ingest replaces instead
  of duplicating, so the pipeline is safe to run repeatedly.
- **`CHROMA_HOST` empty by default; on-disk PersistentClient for local runs.** Local CLI needs
  no running services. The compose api service sets `CHROMA_HOST=http://chroma:8000` in its own
  environment to target the Chroma server. Avoids the "could not connect to Chroma" trap when
  running the CLI outside docker.
- **Per-section source links in the corpus, not a bottom "Further reading" block.** Because the
  MarkdownChunker splits on H2 headings, a source line inside each section is retrieved together
  with that section's chunk, so the agent can always surface a relevant link with an answer. A
  single block at the end would not co-retrieve with a specific fact chunk.
- **Curated for teaching quality, not just authority.** Sources favor good explainers (Pinecone
  Learn, Weaviate, Qdrant, Cohere LLMU, Hugging Face, Anthropic engineering, Simon Willison,
  Evidently, LangChain Academy) with the canonical primary source (papers/specs) included where
  it is the real reference. Every link was web-verified live by the audit agents. Wikipedia and
  SEO content were avoided on purpose.
- **Corpus accuracy is web-audited, not recalled.** All 8 docs were fact-checked against current
  authoritative sources before commit (per the verify-against-docs rule). The corpus is the
  product's ground truth, so a stale claim (the MCP transport bug) would have taught the wrong
  thing and surfaced in grounded answers.
