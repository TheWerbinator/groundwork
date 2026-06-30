# packages/kb

The corpus: curated markdown about AI engineering (LangGraph, hybrid RAG, MCP, model eval,
guardrails, observability, cost optimization). This is what Groundwork retrieves over, which
is why the demo answers teach the same stack the app is built from.

## Current corpus

Eight topic docs, each with `title` + `topic` frontmatter: `rag`, `chunking`, `embeddings`,
`hybrid-search`, `langgraph-agents`, `mcp`, `evaluation`, `guardrails`. They cross-reference
each other and double as the `docs/` teaching content. Ingested by
[packages/ingestion](../ingestion).

Add a topic by dropping a new `*.md` here (with frontmatter) and re-running
`uv run ingestion ingest`.

