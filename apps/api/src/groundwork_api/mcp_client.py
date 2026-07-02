"""MCP-backed retriever.

A drop-in replacement for the in-process HybridRetriever that calls the `search_kb` tool on the
Groundwork MCP server instead. It implements the same `.retrieve(query, top_k)` interface, so the
agent's retriever node does not change: retrieval simply now crosses a protocol boundary (see
docs/mcp.md).

The MCP client library is async; `.retrieve` is sync (the graph nodes are sync), so it bridges
with `asyncio.run`. That is safe here because it is only ever called from a sync context (the CLI,
or the FastAPI endpoint running in a worker thread).
"""

from __future__ import annotations

import asyncio
import json

from ingestion.config import Settings
from retrieval.hybrid import HybridResult


def _content_text(raw) -> str:
    """Unwrap an MCP tool result into its JSON text.

    langchain-mcp-adapters returns the tool output as a list of content blocks,
    e.g. [{"type": "text", "text": "<our json>"}]. This pulls the text out; it also accepts a
    plain string in case a future adapter version returns one directly.
    """
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        return "".join(
            b.get("text", "") for b in raw if isinstance(b, dict) and b.get("type") == "text"
        )
    return json.dumps(raw)


class McpRetriever:
    def __init__(self, settings: Settings) -> None:
        self._url = settings.mcp_url
        self._default_top_k = settings.top_k

    def retrieve(self, query: str, top_k: int | None = None) -> list[HybridResult]:
        top_k = top_k or self._default_top_k
        raw = asyncio.run(self._search(query, top_k))
        rows = json.loads(_content_text(raw))
        return [
            HybridResult(
                id=row["id"],
                text=row["text"],
                metadata={"source": row["source"], "heading": row["heading"]},
                score=row["score"],
            )
            for row in rows
        ]

    async def _search(self, query: str, top_k: int):
        # Imported lazily so `direct` mode never needs the MCP client installed at call time.
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient(
            {"groundwork": {"transport": "streamable_http", "url": self._url}}
        )
        tools = await client.get_tools()
        search = next(t for t in tools if t.name == "search_kb")
        return await search.ainvoke({"query": query, "top_k": top_k})
