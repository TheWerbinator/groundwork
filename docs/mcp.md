# MCP: retrieval over a protocol boundary

> A guided walkthrough of [`apps/mcp`](../apps/mcp) and the client in
> [`apps/api`](../apps/api). For the concept, see [packages/kb/mcp.md](../packages/kb/mcp.md);
> this page shows how our code puts the knowledge-base search behind a Model Context Protocol
> server and has the agent call it as a client.

## What you'll learn

- What an MCP server, client, and tool are, in running code.
- Why moving retrieval behind a protocol boundary is worth the extra hop.
- How the agent's retriever node stays unchanged while retrieval crosses a process boundary.

## Before and after

Through Phase 5, the retriever node called `HybridRetriever` **in-process**:

```
retriever node  ->  HybridRetriever.retrieve(...)      # a Python function call
```

Phase 6 puts that search behind an MCP **tool** on a separate server:

```
retriever node  ->  McpRetriever.retrieve(...)  --MCP over HTTP-->  search_kb tool  ->  HybridRetriever
   (apps/api, the client)                                          (apps/mcp, the server)
```

The agent no longer imports the retriever. It calls a tool across a protocol. That is the whole
idea of MCP: the tool runs in its own process, with its own dependencies and permissions, and any
MCP client can use it.

## The server

[`apps/mcp/src/groundwork_mcp/server.py`](../apps/mcp/src/groundwork_mcp/server.py) is a FastMCP
server exposing one tool:

```python
mcp = FastMCP("groundwork-kb", host="127.0.0.1", port=9000)

@mcp.tool()
def search_kb(query: str, top_k: int = 5) -> str:
    """Search the knowledge base ... Returns a JSON array of {id, text, source, heading, score}."""
    hits = _get_retriever().retrieve(query, top_k=top_k)
    return json.dumps([...])
```

`@mcp.tool()` is the entire tool definition: the function signature *is* the schema (no JSON
Schema to hand-write). The server runs over **streamable-http** by default (`mcp.run(...)`),
serving at `http://127.0.0.1:9000/mcp`; `MCP_TRANSPORT=stdio` switches to stdio for a client that
spawns the server as a subprocess.

## The client

[`apps/api/src/groundwork_api/mcp_client.py`](../apps/api/src/groundwork_api/mcp_client.py)
`McpRetriever` implements the same `.retrieve(query, top_k)` interface the retriever node already
uses, so nothing in the graph changes. Under the hood it uses `langchain-mcp-adapters`:

```python
client = MultiServerMCPClient({"groundwork": {"transport": "streamable_http", "url": ...}})
tools = await client.get_tools()
search = next(t for t in tools if t.name == "search_kb")
result = await search.ainvoke({"query": query, "top_k": top_k})
```

Two real details worth knowing (both discovered by running it, not reading about it):

- **The client is async; the node is sync.** `.retrieve` bridges with `asyncio.run`, which is
  safe because it is only called from sync contexts (the CLI, or the FastAPI endpoint in a worker
  thread).
- **The tool result is wrapped.** `ainvoke` returns a list of content blocks
  (`[{"type": "text", "text": "<our json>"}]`), so `_content_text` unwraps the text before
  `json.loads`. The unit test pins this shape.

## Which backend runs is a config switch

`RETRIEVAL_BACKEND` (`direct` | `mcp`) selects the path in `service._build_retriever`. Default is
`direct`, so the agent runs with zero extra processes; flip to `mcp` to route retrieval over the
protocol. The graph, the guards, and the critic loop are identical either way.

## Run it

```bash
# terminal 1: start the MCP server
cd apps/mcp && uv run groundwork-mcp        # streamable-http on 127.0.0.1:9000/mcp

# terminal 2: run the agent with retrieval over MCP
cd apps/api
RETRIEVAL_BACKEND=mcp MCP_URL=http://127.0.0.1:9000/mcp \
  uv run groundwork-api ask "how does reciprocal rank fusion work?" --trace
```

The trace looks identical to the direct run, because the interface is identical. The difference is
that the `retriever` node's chunks arrived over MCP.

## Why bother (the honest version)

For a single app calling its own retriever, an in-process call is simpler and this hop adds
latency. MCP earns its place when the tool must be reused across clients, run with different
permissions or in a different language, or be swapped without touching the agent, and as the
standard interface a future multi-agent supervisor's sub-agents would share. Here it is built to
teach the boundary and to make the "connect agents to internal tools" capability real; the config
switch keeps the simple path available.

## Try this

1. **Watch the boundary.** Run with `RETRIEVAL_BACKEND=mcp` and no server running; see the client
   fail to connect. Start the server; see it work. The retrieval now depends on a separate process.
2. **Add a second tool.** Add a `list_topics()` tool to the server that returns the KB's topics,
   re-run, and note the client can discover it via `get_tools()` with no client code change.

## Design choices

The reasoning (streamable-http default, same `.retrieve` interface, `direct` default backend,
async-to-sync bridge) is under "Phase 6 decisions" in [DECISIONS.md](../DECISIONS.md).

## Where it goes next

- [Phase 7] the **Rust rerank** service becomes a second internal service the pipeline calls.
- A future multi-agent supervisor (backlog) would give each sub-agent MCP tools like this one.
