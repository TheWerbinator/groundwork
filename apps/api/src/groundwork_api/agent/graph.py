"""Wiring the nodes into a LangGraph state graph.

The graph for v1 is linear:

    START -> planner -> retriever -> drafter -> END

Each arrow is an edge; each box is a node. Because the flow is a graph rather than a hidden
loop, you can draw it, stream it, and test each node in isolation. Phase 5 turns the straight
line into a loop by adding a critic node and a conditional edge back to the retriever. See
docs/agents.md and packages/kb/langgraph-agents.md.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from groundwork_api.agent.nodes import make_drafter, make_planner, make_retriever
from groundwork_api.agent.state import AgentState


def build_agent(llm, retriever, top_k: int = 5):
    """Build and compile the agent graph.

    Args:
        llm: a chat model with `.invoke(messages) -> object with .content` (real provider in
            production, a fake in tests).
        retriever: a HybridRetriever-like object with `.retrieve(query, top_k)`.
        top_k: how many chunks to ground the answer in.

    Returns the compiled graph; call `.invoke(initial_state)` or `.stream(...)` on it.
    """
    builder = StateGraph(AgentState)

    builder.add_node("planner", make_planner(llm))
    builder.add_node("retriever", make_retriever(retriever, top_k))
    builder.add_node("drafter", make_drafter(llm))

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "retriever")
    builder.add_edge("retriever", "drafter")
    builder.add_edge("drafter", END)

    return builder.compile()


def initial_state(question: str) -> dict:
    """A fresh state for one question. Reducer-backed keys start empty; overwrite keys start
    blank and are filled by their node."""
    return {
        "question": question,
        "search_query": "",
        "chunks": [],
        "answer": "",
        "citations": [],
        "notes": [],
    }
