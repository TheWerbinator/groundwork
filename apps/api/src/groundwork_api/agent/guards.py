"""Guardrail nodes: deterministic checks on the input and output paths of the graph.

These nodes are thin: they call the pure functions in `groundwork_api.guardrails` and write the
verdict into the state. Keeping the logic in pure functions is what makes the guardrails testable
in isolation; the nodes just adapt them to the graph.
"""

from __future__ import annotations

from groundwork_api.agent.state import AgentState
from groundwork_api.guardrails import check_input, check_output

REFUSAL = (
    "I can't help with that request. It looks like it may be trying to override the assistant's "
    "instructions (possible prompt injection). Please rephrase it as a genuine question about AI "
    "engineering."
)


def input_guard(state: AgentState) -> dict:
    """Screen the question: redact PII (forward the redacted text) and block injection.

    If blocked, this node also writes the refusal answer, because a blocked request short-circuits
    straight to END (see the conditional edge in graph.py) and never reaches the drafter.
    """
    verdict = check_input(state["question"])
    if verdict.blocked:
        return {
            "blocked": True,
            "answer": REFUSAL,
            "citations": [],
            "flags": verdict.flags,
            "notes": [f"input_guard: BLOCKED ({', '.join(verdict.flags)})"],
        }
    note = "input_guard: clean"
    if verdict.flags:
        note = f"input_guard: redacted ({', '.join(verdict.flags)})"
    return {
        "blocked": False,
        "question": verdict.redacted_question,
        "flags": verdict.flags,
        "notes": [note],
    }


def output_guard(state: AgentState) -> dict:
    """Enforce grounding and scan the answer for leaked PII before it reaches the user."""
    verdict = check_output(state["answer"], state["chunks"])
    updates: dict = {
        "grounded": verdict.grounded,
        "flags": verdict.flags,
        "notes": [
            f"output_guard: grounded={verdict.grounded}"
            + (f" flags={verdict.flags}" if verdict.flags else "")
        ],
    }
    if verdict.redacted_answer != state["answer"]:
        updates["answer"] = verdict.redacted_answer
    return updates


def route_after_input(state: AgentState) -> str:
    """Conditional edge: a blocked request skips the whole pipeline; a clean one proceeds."""
    return "blocked" if state["blocked"] else "ok"
