---
title: Guardrails and safety controls
topic: guardrails
---

# Guardrails and safety controls

Guardrails are deterministic checks placed around a model to keep its inputs and outputs
within policy. They are deterministic on purpose: a model cannot be trusted to police itself,
so the controls that enforce safety and compliance should be ordinary code with predictable
behavior, sitting on the input and output paths.

_Source: [Guardrails AI docs](https://www.guardrailsai.com/docs) - a framework that wraps input/output validators (PII, grounding, toxicity) as deterministic code around the model._

## Input guardrails

Input checks run before the model sees the request. They detect and redact personally
identifiable information so secrets are not embedded or logged (a concern OWASP files
separately as Sensitive Information Disclosure), and they screen for prompt injection, where
text tries to override the system's instructions. Injection comes in two forms: direct, in the
user's typed query, and indirect, carried inside content the system pulls in. A retrieved
document is untrusted content, so injection screening must cover the context, not only the
query.

_Source: [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) - defines direct versus indirect injection and standard mitigations._

## The lethal trifecta

Indirect injection turns dangerous when three capabilities meet in one system: access to
private data, exposure to untrusted content, and the ability to send data outward. With all
three, a malicious instruction hidden in a retrieved document can make the agent read secrets
and exfiltrate them. This framing explains why guardrails extend past text filtering into tool
and output controls: remove any one leg of the trifecta and the attack loses its payoff.

_Source: [Simon Willison: The lethal trifecta](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) - example-driven explanation from the person who coined "prompt injection."_

## Output guardrails

Output checks run on the model's answer before it reaches the user. In a RAG system the most
important is grounding enforcement: verify that the answer cites retrieved chunks and that its
claims are supported by them, and reject or flag answers that introduce unsupported facts.
Output checks also scan for leaked PII and for content that violates policy.

_Source: [NeMo Guardrails: Hallucinations and fact-checking](https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/guardrail-catalog/fact-checking.html) - an implementation of the output rail that enforces grounding in retrieved chunks._

## Determinism, layering, and limits

A guardrail should give the same verdict on the same input every time, which makes it
testable and auditable in a way a model is not. Guardrails layer: an input filter, a
retrieval-time filter, and an output validator each catch different failures, and the cost of
running all three is small next to the cost of one bad answer reaching a user. They are still
defense-in-depth, not a guarantee. Because an LLM is stochastic, prompt injection has no
absolute fix, so guardrails are paired with least-privilege tooling and human approval for
high-risk actions rather than relied on alone.

## Compliance and bias

Privacy regulation requires that personal data be handled deliberately, which is exactly what
PII detection and redaction provide a hook for. Bias is harder because it is statistical, but
the same machinery helps: a golden set that includes sensitive cases, plus output checks for
disallowed content, turns a vague goal into specific tests that either pass or fail.

_Source: [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) - the full risk taxonomy these controls map onto._

See also: rag, evaluation, mcp.
