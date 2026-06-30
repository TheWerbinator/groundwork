"""Agent graph tests with a fake LLM and fake retriever. No network, no API keys."""

from __future__ import annotations

from types import SimpleNamespace

from retrieval.hybrid import HybridResult

from groundwork_api.agent.graph import build_agent, initial_state


class FakeChatModel:
    """Returns a planner query or a drafter answer depending on the system prompt."""

    def invoke(self, messages):
        system = messages[0][1].lower()
        if "search query" in system:
            return SimpleNamespace(content="reciprocal rank fusion k constant")
        return SimpleNamespace(
            content="RRF merges ranked lists by summing 1/(k+rank) [hybrid-search]."
        )


class FakeRetriever:
    def __init__(self, hits):
        self._hits = hits

    def retrieve(self, query, top_k):
        return self._hits[:top_k]


def _hits():
    return [
        HybridResult(
            id="hybrid-search:1",
            text="Reciprocal Rank Fusion merges by rank, 1/(k+rank), k=60.",
            metadata={"source": "hybrid-search", "heading": "Reciprocal Rank Fusion"},
            score=0.033,
        ),
        HybridResult(
            id="hybrid-search:0",
            text="Hybrid search combines dense and sparse retrieval.",
            metadata={"source": "hybrid-search", "heading": "Dense versus sparse"},
            score=0.031,
        ),
    ]


def _graph():
    return build_agent(FakeChatModel(), FakeRetriever(_hits()), top_k=2)


def test_graph_runs_end_to_end():
    state = _graph().invoke(initial_state("how does rrf work?"))
    assert state["search_query"]  # planner ran
    assert len(state["chunks"]) == 2  # retriever ran
    assert "RRF" in state["answer"]  # drafter ran
    assert state["chunks"][0]["source"] == "hybrid-search"


def test_citations_are_unique_and_from_retrieved_sources():
    state = _graph().invoke(initial_state("rrf?"))
    cites = state["citations"]
    # Two chunks, same source, different headings -> two distinct citations.
    assert len(cites) == 2
    assert {c["source"] for c in cites} == {"hybrid-search"}
    assert {c["heading"] for c in cites} == {"Reciprocal Rank Fusion", "Dense versus sparse"}


def test_notes_reducer_accumulates_across_nodes():
    state = _graph().invoke(initial_state("rrf?"))
    # The `add` reducer appends each node's note instead of overwriting: one per node.
    assert len(state["notes"]) == 3
    assert state["notes"][0].startswith("planner")
    assert state["notes"][1].startswith("retriever")
    assert state["notes"][2].startswith("drafter")


def test_stream_emits_one_event_per_node():
    seen = []
    for event in _graph().stream(initial_state("rrf?"), stream_mode="updates"):
        seen.extend(event.keys())
    assert seen == ["planner", "retriever", "drafter"]
