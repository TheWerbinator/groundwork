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

- _(none beyond D0/D1 yet)_
