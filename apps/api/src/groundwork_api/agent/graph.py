"""Wiring the nodes into a LangGraph state graph.

The graph (Phase 5) guards both ends AND reflects on its own answer:

    START -> input_guard --(blocked)--> END
                  |
                (ok)
                  v
         planner -> retriever -> drafter -> critic --(sufficient / gave up)--> output_guard -> END
            ^                                  |
            |                            (insufficient)
            +----------------------------------+

Two CONDITIONAL edges drive the control flow. `input_guard` short-circuits a blocked request to
END. `critic` (an LLM-as-a-judge) sends a weak answer BACK to the planner to try again, up to
`max_retries` times; a sufficient answer (or an exhausted retry budget) proceeds to
`output_guard`. The loop is bounded by the retry count in the state, so it cannot run forever.
See docs/agents.md and packages/kb/langgraph-agents.md.
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from groundwork_api.agent.guards import input_guard, output_guard, route_after_input
from groundwork_api.agent.nodes import (
    make_critic,
    make_drafter,
    make_planner,
    make_retriever,
)
from groundwork_api.agent.state import AgentState


def build_agent(llm, retriever, top_k: int = 5, max_retries: int = 1):
    """Build and compile the agent graph.

    Args:
        llm: a chat model with `.invoke(messages) -> object with .content` (real provider in
            production, a fake in tests).
        retriever: a HybridRetriever-like object with `.retrieve(query, top_k)`.
        top_k: how many chunks to ground the answer in.
        max_retries: how many times the critic may send a weak answer back to re-plan.

    Returns the compiled graph; call `.invoke(initial_state)` or `.stream(...)` on it.
    """

    def route_after_critic(state: AgentState) -> str:
        """Conditional edge: loop back to re-plan unless the answer is sufficient or the retry
        budget is spent. `retries` counts critic rejections; we re-plan while it is within
        `max_retries`. `max_retries` is captured here so the router stays a function of state."""
        if state["critic_sufficient"] or state["retries"] > max_retries:
            return "done"
        return "retry"

    builder = StateGraph(AgentState)

    builder.add_node("input_guard", input_guard)
    builder.add_node("planner", make_planner(llm))
    builder.add_node("retriever", make_retriever(retriever, top_k))
    builder.add_node("drafter", make_drafter(llm))
    builder.add_node("critic", make_critic(llm))
    builder.add_node("output_guard", output_guard)

    builder.add_edge(START, "input_guard")
    # Conditional edge: blocked input -> END (refusal), clean input -> planner.
    builder.add_conditional_edges(
        "input_guard", route_after_input, {"blocked": END, "ok": "planner"}
    )
    builder.add_edge("planner", "retriever")
    builder.add_edge("retriever", "drafter")
    builder.add_edge("drafter", "critic")
    # Conditional edge: weak answer -> back to planner; good/exhausted -> output_guard.
    builder.add_conditional_edges(
        "critic", route_after_critic, {"retry": "planner", "done": "output_guard"}
    )
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
        "retries": 0,
        "critic_sufficient": False,
        "critic_feedback": "",
    }
