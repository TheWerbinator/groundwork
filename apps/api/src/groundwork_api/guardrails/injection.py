"""Prompt-injection detection.

A deterministic screen for the common shapes of a prompt-injection attempt: text trying to
override the system's instructions, extract the system prompt, or hijack the assistant's role
(see packages/kb/guardrails.md). Each pattern is paired with a short label so a match explains
itself in the guardrail flags.

Scope note: this screens the *user's question*. Indirect injection carried inside retrieved
documents is a separate concern; here the corpus is trusted content we authored, so retrieval-
time screening is left as a documented extension. Like PII regex, this is a high-signal floor,
not a complete defense; it favors catching blatant attempts over subtle ones.
"""

from __future__ import annotations

import re

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("override_instructions", re.compile(
        r"\b(ignore|disregard|forget)\b.{0,30}\b(previous|prior|above|earlier|your)\b"
        r".{0,20}\b(instruction|instructions|prompt|prompts|rules?)\b", re.I)),
    ("reveal_system_prompt", re.compile(
        r"\b(reveal|show|print|repeat|output)\b.{0,30}\b(system|initial|hidden|your)\b"
        r".{0,20}\b(prompt|instructions?|rules?)\b", re.I)),
    ("role_hijack", re.compile(
        r"\b(you are now|pretend to be|act as if|from now on you|new persona)\b", re.I)),
    ("jailbreak", re.compile(r"\b(jailbreak|DAN mode|developer mode|do anything now)\b", re.I)),
    ("override_verb", re.compile(
        r"\b(override|bypass|disable)\b.{0,20}\b(instruction|instructions|rules?|guardrails?|"
        r"safety)\b", re.I)),
]


def detect_injection(text: str) -> list[str]:
    """Return labels of injection patterns found in the text. Empty list means clean."""
    return [label for label, pattern in _PATTERNS if pattern.search(text)]
