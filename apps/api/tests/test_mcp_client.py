"""MCP client parsing tests. No server, no network (the tool call is stubbed)."""

from __future__ import annotations

import json

from ingestion.config import get_settings

from groundwork_api.mcp_client import McpRetriever, _content_text


def test_content_text_unwraps_content_blocks():
    raw = [{"type": "text", "text": '[{"id": "rag:0"}]'}]
    assert _content_text(raw) == '[{"id": "rag:0"}]'


def test_content_text_passes_through_a_string():
    assert _content_text("already text") == "already text"


def test_mcp_retriever_maps_tool_result_to_hybrid_results(monkeypatch):
    retriever = McpRetriever(get_settings())
    rows = [
        {"id": "rag:0", "text": "t", "source": "rag", "heading": "Why RAG", "score": 0.03}
    ]
    block = [{"type": "text", "text": json.dumps(rows)}]

    async def fake_search(query, top_k):
        return block

    monkeypatch.setattr(retriever, "_search", fake_search)
    hits = retriever.retrieve("q", top_k=1)
    assert len(hits) == 1
    assert hits[0].id == "rag:0"
    assert hits[0].source == "rag"  # HybridResult property from metadata
    assert hits[0].heading == "Why RAG"
    assert hits[0].score == 0.03
