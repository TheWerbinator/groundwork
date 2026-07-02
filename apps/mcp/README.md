# apps/mcp

A Model Context Protocol server that exposes the knowledge-base search as an MCP **tool**. The
agent connects as an MCP client and calls `search_kb` over the protocol boundary instead of an
in-process function.

- `search_kb(query, top_k)` - runs hybrid retrieval ([packages/retrieval](../../packages/retrieval))
  and returns a JSON array of `{id, text, source, heading, score}`.
- FastMCP server ([server.py](src/groundwork_mcp/server.py)); streamable-http by default,
  `MCP_TRANSPORT=stdio` for a spawn-the-server client.

## Run

```bash
cd apps/mcp
uv sync
uv run groundwork-mcp        # streamable-http on http://127.0.0.1:9000/mcp
```

Then point the agent at it (in `apps/api`):

```bash
RETRIEVAL_BACKEND=mcp MCP_URL=http://127.0.0.1:9000/mcp \
  uv run groundwork-api ask "how does reciprocal rank fusion work?" --trace
```

See [docs/mcp.md](../../docs/mcp.md) for the walkthrough (server, client, and why the boundary).

**Built in:** Phase 6.
