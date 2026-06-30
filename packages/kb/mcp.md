---
title: Model Context Protocol
topic: mcp
---

# Model Context Protocol

The Model Context Protocol (MCP) is an open standard for connecting AI agents to tools and
data sources over a defined protocol rather than through in-process function calls. An MCP
server exposes capabilities; an MCP client, running inside a host application, discovers and
calls them. The point is a stable contract between the agent and its tools. The claims below
track the current specification revision, 2025-11-25.

## Roles: host, client, server

MCP has three roles, and conflating them causes confusion. The **host** is the LLM application
the user interacts with (an IDE, a chat app, an agent runtime); it initiates connections. A
**client** is a connector living inside the host, one per server, that speaks the protocol. A
**server** is the program that exposes tools and data. So "the agent calls a tool" really
means the host's client calls the server.

_Source: [MCP: Architecture](https://modelcontextprotocol.io/docs/learn/architecture) - official conceptual walkthrough of hosts, clients, servers, and lifecycle._

## Server primitives

An MCP server advertises three kinds of primitives. **Tools** are callable functions the agent
can invoke, such as "search the knowledge base." **Resources** are readable data the agent can
pull in as context, such as a document by URI. **Prompts** are reusable templates the server
offers. A client connects, lists what the server exposes, and calls tools on the agent's
behalf.

Clients can expose primitives too. A client may offer **sampling** (let the server ask the
host to run an LLM completion), **roots** (tell the server which filesystem or URI boundaries
it may touch), and **elicitation** (let the server request structured input from the user).
These are how a server gets controlled access back into the host.

_Source: [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25) - the authoritative list of server and client features._

## Connection lifecycle

A connection is stateful and opens with capability negotiation: the client sends an
`initialize` request, the two sides agree on protocol version and which features each supports,
and the client confirms with an initialized notification. Everything else, listing tools,
calling them, streaming results, happens within that negotiated session.

_Source: [MCP: Getting Started](https://modelcontextprotocol.io/docs/getting-started/intro) - plain-language intro with the "USB-C port for AI" analogy and the lifecycle._

## Transports

MCP messages are JSON-RPC 2.0. The spec defines two standard transports. **stdio**: the host
launches the server as a subprocess and they exchange newline-delimited JSON-RPC over standard
input and output, which suits local servers. **Streamable HTTP**: the server runs behind a
single HTTP endpoint that accepts POST requests and may optionally use server-sent events to
stream multiple messages back, which suits remote servers. The older standalone HTTP+SSE
transport was replaced by Streamable HTTP in revision 2025-03-26 and remains only for
backward compatibility with pre-2025 servers. The protocol is the same across transports; only
the framing changes.

_Source: [MCP Specification 2025-11-25: Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) - defines stdio and Streamable HTTP and marks HTTP+SSE legacy._

## Security posture

Because an MCP server can expose real tools and data, every tool call crosses a trust
boundary, and trust runs both ways. A server should expose the least it needs to, validate
every argument, and treat the calling agent as untrusted. The host must equally protect the
user from servers: the spec's principles stress user consent and control, data privacy, and
tool safety, and they warn that a tool's own description and annotations are untrusted unless
the server is trusted. Guard the server from the agent and the user from the server.

_Source: [Anthropic: Introducing MCP](https://www.anthropic.com/news/model-context-protocol) - the motivation and the M-by-N integration problem MCP solves._

See also: langgraph-agents, guardrails.
