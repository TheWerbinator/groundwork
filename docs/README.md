# docs

A learning path through Groundwork. These pages teach **how this repo's code works**, stage by
stage. They are distinct from two neighbors:

- the [knowledge base](../packages/kb) teaches the **concepts** generically (what RAG is, how
  RRF works), and is also the corpus the app retrieves over;
- [DECISIONS.md](../DECISIONS.md) records **why** each choice was made.

These walkthroughs connect the two: concept -> our code -> run it yourself -> exercises.

## Read in order

1. [ingestion.md](ingestion.md) - turning documents into retrievable chunks (load, chunk,
   embed, store). *Built in Phase 1.*
2. [retrieval.md](retrieval.md) - hybrid search: dense + sparse + reciprocal-rank fusion.
   *Built in Phase 2.*
3. [agents.md](agents.md) - the LangGraph agent: planner, retriever, drafter, critic, and the
   self-reflection loop. *Built in Phase 3.*

## Planned (filled in alongside the phase that builds the concept)

- `mcp.md` - what MCP is and why a protocol boundary beats in-process tools *(Phase 6)*
- `eval.md` - evaluating foundation models; the cost / latency / accuracy frontier *(Phase 10)*
- `guardrails.md` - deterministic safety controls and where they sit *(Phase 4)*
- `observability.md` - tracing reasoning chains with OpenTelemetry *(Phase 9)*
- `cost.md` - prompt + semantic caching and token-cost optimization *(Phase 9)*
- `cloud.md` - AWS deployment; Azure / GCP comparison *(Phase 11)*

Each page also surveys the alternatives the brief asks about (Pinecone vs Chroma, AutoGen /
CrewAI vs LangGraph, and so on).
