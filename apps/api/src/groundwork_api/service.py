"""Runtime wiring: build the real agent once and expose simple answer/stream methods.

This is the seam between the pure agent graph and the outside world (the REST app and the CLI).
Keeping it here means the FastAPI route and the CLI share exactly one construction path, and
tests can swap an `AgentService` for a fake without touching either.
"""

from __future__ import annotations

from collections.abc import Iterator

from ingestion.config import Settings, get_settings
from retrieval.hybrid import HybridRetriever

from groundwork_api.agent.graph import build_agent, initial_state
from groundwork_api.llm import build_chat_model


class AgentService:
    def __init__(self, graph) -> None:
        self._graph = graph

    def answer(self, question: str) -> dict:
        """Run the graph to completion; return the final state."""
        return self._graph.invoke(initial_state(question))

    def stream(self, question: str) -> Iterator[dict]:
        """Yield one event per node as it finishes ({node_name: state_update}), for --trace."""
        yield from self._graph.stream(initial_state(question), stream_mode="updates")


def _build_retriever(settings: Settings):
    """Direct in-process retrieval, or retrieval over the MCP protocol, per config."""
    if settings.retrieval_backend == "mcp":
        from groundwork_api.mcp_client import McpRetriever

        return McpRetriever(settings)
    return HybridRetriever(settings)


def build_service(settings: Settings | None = None) -> AgentService:
    settings = settings or get_settings()
    llm = build_chat_model(settings)
    retriever = _build_retriever(settings)
    graph = build_agent(
        llm, retriever, top_k=settings.top_k, max_retries=settings.max_retries
    )
    return AgentService(graph)
