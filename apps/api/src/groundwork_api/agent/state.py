"""The agent's state.

In LangGraph the state is a typed dictionary threaded through every node. A node receives the
state and returns a dict of updates; LangGraph merges those updates back in. How a key is merged
is decided by its *reducer*:

- A key with no reducer is OVERWRITTEN by each update (the default). `question`, `search_query`,
  `answer`, and `chunks` work this way: each is written once by one node.
- A key annotated with a reducer is COMBINED. `notes` below uses `operator.add`, so when a node
  returns `{"notes": ["did X"]}`, that list is appended to the running notes instead of replacing
  them. That is how state accumulates across the graph.

`notes` is a teaching device here (a human-readable trace of what each node did, surfaced by the
`--trace` CLI), but the reducer mechanism is exactly what the Phase 5 critic loop will use to
accumulate retries. See docs/agents.md and packages/kb/langgraph-agents.md.
"""

from __future__ import annotations

from operator import add
from typing import Annotated, TypedDict


class Chunk(TypedDict):
    """A retrieved chunk, flattened to plain data so the state stays JSON-serializable."""

    id: str
    text: str
    source: str
    heading: str
    score: float


class Citation(TypedDict):
    source: str
    heading: str


class AgentState(TypedDict):
    question: str  # the user's question (input; PII-redacted by the input guard)
    search_query: str  # planner's focused query for retrieval
    chunks: list[Chunk]  # retriever's grounding context
    answer: str  # drafter's grounded answer
    citations: list[Citation]  # sources the answer is grounded in
    notes: Annotated[list[str], add]  # accumulated step log (reducer: append, do not overwrite)

    # Guardrails (Phase 4)
    blocked: bool  # input guard refused the request (e.g. prompt injection)
    grounded: bool  # output guard confirmed the answer cites retrieved sources
    flags: Annotated[list[str], add]  # guardrail findings, accumulated across guard nodes
