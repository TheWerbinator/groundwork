"""The agent's nodes.

Each node is a plain function: it takes the state and returns a dict of updates. Nodes are built
by small factory functions that close over their dependencies (the LLM, the retriever), which
keeps the nodes themselves pure and easy to test with fakes. The three nodes map one-to-one to
the RAG stages: planner (decide what to retrieve), retriever (fetch context), drafter (generate a
grounded answer). See docs/agents.md for the guided walkthrough.
"""

from __future__ import annotations

from collections.abc import Callable

from groundwork_api.agent.prompts import (
    DRAFTER_SYSTEM,
    PLANNER_SYSTEM,
    drafter_user_prompt,
)
from groundwork_api.agent.state import AgentState

Node = Callable[[AgentState], dict]


def make_planner(llm) -> Node:
    """Planner: turn the user's question into a focused retrieval query.

    A trivial planner could just retrieve on the raw question. Using the LLM to rewrite it is the
    smallest honest example of 'autonomous planning': the agent decides how to search, and later
    phases extend this node to choose tools or decompose the question.
    """

    def planner(state: AgentState) -> dict:
        question = state["question"]
        response = llm.invoke(
            [("system", PLANNER_SYSTEM), ("human", question)]
        )
        query = (response.content or "").strip() or question
        return {"search_query": query, "notes": [f"planner: search query = {query!r}"]}

    return planner


def make_retriever(retriever, top_k: int) -> Node:
    """Retriever: run hybrid search for the planned query and flatten the hits into state.

    `retriever` is the HybridRetriever from packages/retrieval. The node depends only on its
    `.retrieve(query, top_k)` method, so a fake retriever stands in for it in tests.
    """

    def retrieve(state: AgentState) -> dict:
        hits = retriever.retrieve(state["search_query"], top_k=top_k)
        chunks = [
            {
                "id": hit.id,
                "text": hit.text,
                "source": hit.source,
                "heading": hit.heading,
                "score": hit.score,
            }
            for hit in hits
        ]
        return {
            "chunks": chunks,
            "notes": [f"retriever: {len(chunks)} chunks for {state['search_query']!r}"],
        }

    return retrieve


def make_drafter(llm) -> Node:
    """Drafter: write a grounded answer from the retrieved chunks and cite the sources.

    Citations are derived deterministically from the chunks that were placed in the prompt (the
    grounding set), so the answer always points at real, retrieved sources. A later phase can
    tighten this to only the sources the model actually used.
    """

    def drafter(state: AgentState) -> dict:
        chunks = state["chunks"]
        response = llm.invoke(
            [
                ("system", DRAFTER_SYSTEM),
                ("human", drafter_user_prompt(state["question"], chunks)),
            ]
        )
        answer = (response.content or "").strip()

        citations: list[dict] = []
        seen: set[tuple[str, str]] = set()
        for chunk in chunks:
            key = (chunk["source"], chunk["heading"])
            if key not in seen:
                seen.add(key)
                citations.append({"source": chunk["source"], "heading": chunk["heading"]})

        return {
            "answer": answer,
            "citations": citations,
            "notes": [f"drafter: answered from {len(citations)} sources"],
        }

    return drafter
