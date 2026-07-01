"""Deterministic guardrails: input and output checks around the agent.

Guardrails are ordinary, deterministic code, not a model policing itself, so they give the same
verdict on the same input every time and are fully unit-testable (see
packages/kb/guardrails.md). This package holds the pure logic; the graph nodes in
`agent/guards.py` call it.
"""

from groundwork_api.guardrails.checks import (
    InputVerdict,
    OutputVerdict,
    check_input,
    check_output,
)

__all__ = ["InputVerdict", "OutputVerdict", "check_input", "check_output"]
