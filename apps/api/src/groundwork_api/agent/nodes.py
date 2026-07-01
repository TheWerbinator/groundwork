"""The agent's nodes.

Each node is a plain function: it takes the state and returns a dict of updates. Nodes are built
by small factory functions that close over their dependencies (the LLM, the retriever), which
keeps the nodes themselves pure and easy to test with fakes. The three nodes map one-to-one to
the RAG stages: planner (decide what to retrieve), retriever (fetch context), drafter (generate a
grounded answer). See docs/agents.md for the guided walkthrough.
"""

from __future__ import annotations

import re
from collections.abc import Callable

from groundwork_api.agent.prompts import (
    CRITIC_SYSTEM,
    DRAFTER_SYSTEM,
    PLANNER_SYSTEM,
    critic_user_prompt,
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
        feedback = state.get("critic_feedback", "")
        if feedback:
            # On a retry, the planner re-plans using the critic's reason, so the next retrieval
            # goes after what the last attempt missed.
            human = (
                f"{question}\n\nA previous answer was judged insufficient because: {feedback}\n"
                "Write an improved search query that would retrieve what was missing."
            )
        else:
            human = question
        response = llm.invoke([("system", PLANNER_SYSTEM), ("human", human)])
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


def _parse_verdict(text: str) -> tuple[bool, str]:
    """Parse the critic's two-line reply. Unparseable output fails OPEN (treated as sufficient)
    so a malformed critique cannot trap the agent in a retry loop."""
    verdict = re.search(r"VERDICT:\s*(SUFFICIENT|INSUFFICIENT)", text, re.I)
    reason = re.search(r"REASON:\s*(.+)", text, re.I)
    sufficient = verdict.group(1).upper() == "SUFFICIENT" if verdict else True
    return sufficient, (reason.group(1).strip() if reason else "")


def make_critic(llm) -> Node:
    """Critic: an LLM-as-a-judge that reads the question, the context, and the draft, and decides
    whether the answer is grounded and complete.

    This is the self-reflection step: a second LLM role evaluating the drafter's work. On an
    INSUFFICIENT verdict it records the reason and bumps the retry count; the conditional edge in
    graph.py then routes back to the planner to try again (see docs/agents.md).
    """

    def critic(state: AgentState) -> dict:
        response = llm.invoke(
            [
                ("system", CRITIC_SYSTEM),
                ("human", critic_user_prompt(state["question"], state["chunks"], state["answer"])),
            ]
        )
        sufficient, reason = _parse_verdict((response.content or "").strip())
        if sufficient:
            return {"critic_sufficient": True, "notes": ["critic: SUFFICIENT"]}
        attempt = state["retries"] + 1
        return {
            "critic_sufficient": False,
            "critic_feedback": reason,
            "retries": attempt,
            "notes": [f"critic: INSUFFICIENT ({reason}) -> retry #{attempt}"],
        }

    return critic
