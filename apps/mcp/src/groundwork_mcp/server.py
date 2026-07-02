"""The Groundwork MCP server.

Exposes one tool, `search_kb`, that runs hybrid retrieval over the knowledge base. The agent
connects as an MCP client and calls this tool over the protocol, instead of importing the
retriever in-process. That protocol boundary is the whole point of MCP: the tool can run in its
own process (its own dependencies, its own permissions) and be reused by any client (see
packages/kb/mcp.md and docs/mcp.md).

Run it:
    uv run groundwork-mcp                     # streamable-http on 127.0.0.1:9000/mcp (default)
    MCP_TRANSPORT=stdio uv run groundwork-mcp # stdio, for a client that spawns the server
"""

from __future__ import annotations

import json
import os

from mcp.server.fastmcp import FastMCP

# Host/port come from FastMCP's own settings (env prefix FASTMCP_, e.g. FASTMCP_HOST=0.0.0.0 in
# docker). Defaults suit local runs.
mcp = FastMCP("groundwork-kb", host="127.0.0.1", port=9000)

_retriever = None  # built lazily on first call so import stays cheap


def _get_retriever():
    global _retriever
    if _retriever is None:
        from ingestion.config import get_settings
        from retrieval.hybrid import HybridRetriever

        _retriever = HybridRetriever(get_settings())
    return _retriever


@mcp.tool()
def search_kb(query: str, top_k: int = 5) -> str:
    """Search the Groundwork AI-engineering knowledge base with hybrid (dense + sparse) retrieval.

    Args:
        query: the search query.
        top_k: how many chunks to return.

    Returns a JSON array of objects with keys: id, text, source, heading, score.
    """
    hits = _get_retriever().retrieve(query, top_k=top_k)
    payload = [
        {"id": h.id, "text": h.text, "source": h.source, "heading": h.heading, "score": h.score}
        for h in hits
    ]
    return json.dumps(payload)


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "streamable-http")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
