# apps/api

FastAPI backend hosting the LangGraph agent. The agent answers AI-engineering questions grounded
in the knowledge base, with citations, over a REST endpoint.

## The agent

A LangGraph state graph, guarded on both ends and self-reflecting:

```
START -> input_guard --(blocked)--> END
              |
            (ok)
              v
      planner -> retriever -> drafter -> critic --(ok / gave up)--> output_guard -> END
         ^                                  |
         |                            (insufficient)
         +----------------------------------+
```

- **input_guard** ([agent/guards.py](src/groundwork_api/agent/guards.py)) - deterministic checks:
  redact PII, block prompt injection (a conditional edge sends a blocked request straight to END).
- **planner** ([agent/nodes.py](src/groundwork_api/agent/nodes.py)) - LLM rewrites the question
  into a focused search query (using the critic's feedback on a retry).
- **retriever** - runs hybrid search ([packages/retrieval](../../packages/retrieval)) for that
  query.
- **drafter** - LLM writes a grounded answer from the retrieved chunks and cites the sources.
- **critic** - LLM-as-a-judge; a weak answer loops back to the planner, bounded by `max_retries`.
- **output_guard** - enforce grounding (answer must cite a retrieved source) and scan for leaked
  PII. See [docs/guardrails.md](../../docs/guardrails.md) and [docs/agents.md](../../docs/agents.md).

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

**Built in:** Phase 3 (agent v1 + REST), Phase 4 (guardrails), Phase 5 (self-reflection/critic
loop). MCP tools (Phase 6) and human-in-the-loop (Phase 8) extend this.
