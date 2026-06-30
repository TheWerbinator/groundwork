"""Prompts for the agent's LLM nodes, kept in one place so they are easy to read and tune."""

from __future__ import annotations

PLANNER_SYSTEM = (
    "You turn a user's question into ONE focused search query for a knowledge base about AI "
    "engineering. Output only the query text, no preamble, no quotes. Keep it concise and keep "
    "the distinctive terms from the question."
)

DRAFTER_SYSTEM = (
    "You answer questions about AI engineering using ONLY the provided context passages. "
    "Ground every claim in the context. Cite the sources you use inline with their bracketed "
    "labels, for example [hybrid-search]. If the context does not contain the answer, say so "
    "plainly rather than guessing. Be concise and accurate."
)


def drafter_user_prompt(question: str, chunks: list) -> str:
    """Assemble the retrieved chunks + question into the drafter's prompt.

    This is the 'augment' step of RAG: how the context is formatted, labeled, and ordered is a
    real quality lever (see packages/kb/rag.md). Each chunk is labeled with its source so the
    model can cite it.
    """
    if not chunks:
        return f"Context: (none retrieved)\n\nQuestion: {question}"

    blocks = []
    for chunk in chunks:
        label = chunk["source"]
        if chunk["heading"]:
            label = f"{label} > {chunk['heading']}"
        blocks.append(f"[{chunk['source']}] ({label})\n{chunk['text']}")
    context = "\n\n".join(blocks)
    return f"Context passages:\n\n{context}\n\nQuestion: {question}\n\nAnswer (cite sources):"
