"""Input and output guardrail checks, composed from the PII and injection detectors.

These are the two functions the graph's guard nodes call. Both are pure: same input, same
verdict, every time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from groundwork_api.guardrails.injection import detect_injection
from groundwork_api.guardrails.pii import redact_pii

# A citation looks like [hybrid-search] in the drafted answer.
_CITATION = re.compile(r"\[([a-z0-9][a-z0-9-]*)\]")


@dataclass
class InputVerdict:
    redacted_question: str  # question with any PII replaced, safe to forward
    blocked: bool  # true if the request should be refused (injection detected)
    flags: list[str] = field(default_factory=list)  # human-readable guardrail notes


@dataclass
class OutputVerdict:
    redacted_answer: str  # answer with any leaked PII replaced
    grounded: bool  # true if the answer cites at least one retrieved source
    flags: list[str] = field(default_factory=list)


def check_input(question: str) -> InputVerdict:
    """Screen the user's question. Redact PII (forward the redacted text); block on injection.

    PII is redacted rather than blocked, because a user may legitimately include an address or
    email. Injection is blocked, because it is an attack on the system's instructions.
    """
    redacted, pii_labels = redact_pii(question)
    injections = detect_injection(question)  # detect on the original text

    flags = [f"pii_redacted:{label}" for label in pii_labels]
    flags += [f"injection:{label}" for label in injections]
    return InputVerdict(redacted_question=redacted, blocked=bool(injections), flags=flags)


def check_output(answer: str, chunks: list[dict]) -> OutputVerdict:
    """Enforce grounding and scan for leaked PII on the drafted answer.

    Grounding is the main anti-hallucination control in a RAG system: the answer must cite at
    least one of the sources that were actually retrieved. An answer that cites nothing from the
    context is flagged `ungrounded`.
    """
    redacted, pii_labels = redact_pii(answer)

    cited = {m.lower() for m in _CITATION.findall(answer)}
    sources = {chunk["source"].lower() for chunk in chunks}
    grounded = bool(cited & sources)

    flags = [f"pii_leaked:{label}" for label in pii_labels]
    if not grounded:
        flags.append("ungrounded")
    return OutputVerdict(redacted_answer=redacted, grounded=grounded, flags=flags)
