# apps/api

FastAPI backend hosting the LangGraph agent. The agent answers AI-engineering questions grounded
in the knowledge base, with citations, over a REST endpoint.

## The agent

A LangGraph state graph, guarded on both ends:

```
START -> input_guard --(blocked)--> END
              |
            (ok)
              v
         planner -> retriever -> drafter -> output_guard -> END
```

- **input_guard** ([agent/guards.py](src/groundwork_api/agent/guards.py)) - deterministic checks:
  redact PII, block prompt injection (a conditional edge sends a blocked request straight to END).
- **planner** ([agent/nodes.py](src/groundwork_api/agent/nodes.py)) - LLM rewrites the question
  into a focused search query.
- **retriever** - runs hybrid search ([packages/retrieval](../../packages/retrieval)) for that
  query.
- **drafter** - LLM writes a grounded answer from the retrieved chunks and cites the sources.
- **output_guard** - enforce grounding (answer must cite a retrieved source) and scan for leaked
  PII. See [docs/guardrails.md](../../docs/guardrails.md).

State, nodes, edges, and the `notes` reducer are explained in
[docs/agents.md](../../docs/agents.md) (the learner walkthrough) and
[packages/kb/langgraph-agents.md](../../packages/kb/langgraph-agents.md) (the concept).

The LLM provider (`claude` | `openai` | `ollama`) is chosen by `DEFAULT_PROVIDER`; the agent code
never knows which it got ([llm.py](src/groundwork_api/llm.py)).

## Usage

```bash
cd apps/api
uv sync
# Needs the KB ingested (packages/ingestion: uv run ingestion ingest) and a provider configured.
uv run groundwork-api ask "how does reciprocal rank fusion work?"
uv run groundwork-api ask "..." --trace     # watch the state change node by node
uv run groundwork-api serve                 # REST API at http://localhost:8000 (/docs for OpenAPI)
uv run pytest                               # graph + endpoint tests (fake LLM, no network)
```

`POST /ask {"question": "..."}` returns `{question, search_query, answer, citations, chunks_used}`.

**Built in:** Phase 3 (agent v1 + REST), Phase 4 (guardrails). Self-reflection/critic loop
(Phase 5) and MCP tools (Phase 6) extend this.
