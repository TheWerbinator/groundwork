"""PII detection and redaction.

Deterministic regex detectors for the common, high-signal PII types. This runs on both the
input (so secrets are not embedded in the prompt or logged) and the output (so nothing leaks
back to the user). See packages/kb/guardrails.md.

Honest limitation: regex PII detection is a floor, not a guarantee. It catches well-formed
emails, SSNs, phone numbers, and card-shaped digit runs, and it will miss obfuscated or unusual
formats. A production system would layer a trained NER model on top. The point here is a
deterministic, testable first line of defense.
"""

from __future__ import annotations

import re

# Order matters: more specific / longer patterns first, so a card number is not partially
# eaten by the phone pattern. Each match is replaced by a typed placeholder.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]?){13,16}\b")),
    ("PHONE", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
]


def detect_pii(text: str) -> list[str]:
    """Return the sorted set of PII type labels found in the text (e.g. ['EMAIL', 'SSN'])."""
    found = {label for label, pattern in _PATTERNS if pattern.search(text)}
    return sorted(found)


def redact_pii(text: str) -> tuple[str, list[str]]:
    """Replace detected PII with typed placeholders. Returns (redacted_text, labels_found).

    Patterns are applied in order and each replaces its matches with `[REDACTED_<TYPE>]`, so a
    later pattern cannot re-match text already redacted.
    """
    found: list[str] = []
    redacted = text
    for label, pattern in _PATTERNS:
        if pattern.search(redacted):
            found.append(label)
            redacted = pattern.sub(f"[REDACTED_{label}]", redacted)
    return redacted, found
