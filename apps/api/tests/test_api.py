"""REST endpoint tests. The agent service is overridden with a fake, so no model or index runs."""

from __future__ import annotations

from fastapi.testclient import TestClient

from groundwork_api.app import app, get_service


class FakeService:
    def answer(self, question: str) -> dict:
        return {
            "question": question,
            "search_query": "rrf k constant",
            "answer": "RRF sums 1/(k+rank) [hybrid-search].",
            "citations": [{"source": "hybrid-search", "heading": "Reciprocal Rank Fusion"}],
            "chunks": [{"id": "hybrid-search:1"}],
            "blocked": False,
            "grounded": True,
            "flags": [],
            "retries": 0,
        }


app.dependency_overrides[get_service] = lambda: FakeService()
client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_ask_returns_grounded_answer_shape():
    res = client.post("/ask", json={"question": "how does rrf work?"})
    assert res.status_code == 200
    body = res.json()
    assert body["answer"].startswith("RRF")
    assert body["search_query"] == "rrf k constant"
    assert body["chunks_used"] == 1
    assert body["citations"] == [
        {"source": "hybrid-search", "heading": "Reciprocal Rank Fusion"}
    ]
    assert body["blocked"] is False
    assert body["grounded"] is True
    assert body["flags"] == []
    assert body["retries"] == 0


def test_ask_rejects_empty_question():
    res = client.post("/ask", json={"question": ""})
    assert res.status_code == 422  # pydantic min_length validation
