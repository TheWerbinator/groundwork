"""Wiring the nodes into a LangGraph state graph.

The graph (Phase 4) guards both ends of the pipeline:

    START -> input_guard --(blocked)--> END
                  |
                (ok)
                  v
             planner -> retriever -> drafter -> output_guard -> END

`input_guard` uses a CONDITIONAL edge: a blocked request (e.g. prompt injection) short-circuits
straight to END with a refusal, never touching the model. A clean request flows through the
planner/retriever/drafter, then `output_guard` enforces grounding and scans for leaked PII.

The conditional edge is the same mechanism Phase 5 uses to loop back to the retriever when the
critic rejects an answer. See docs/agents.md, docs/guardrails.md, and
packages/kb/langgraph-agents.md.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from groundwork_api.agent.guards import input_guard, output_guard, route_after_input
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

    builder.add_node("input_guard", input_guard)
    builder.add_node("planner", make_planner(llm))
    builder.add_node("retriever", make_retriever(retriever, top_k))
    builder.add_node("drafter", make_drafter(llm))
    builder.add_node("output_guard", output_guard)

    builder.add_edge(START, "input_guard")
    # Conditional edge: blocked input -> END (refusal), clean input -> planner.
    builder.add_conditional_edges(
        "input_guard", route_after_input, {"blocked": END, "ok": "planner"}
    )
    builder.add_edge("planner", "retriever")
    builder.add_edge("retriever", "drafter")
    builder.add_edge("drafter", "output_guard")
    builder.add_edge("output_guard", END)

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
        "blocked": False,
        "grounded": False,
        "flags": [],
    }
