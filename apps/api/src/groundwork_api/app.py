"""FastAPI app exposing the agent over REST.

One endpoint, POST /ask, plus a health check. FastAPI generates the OpenAPI schema from the
pydantic models below, which is what gives the Next.js frontend (Phase 8) a typed client for
free. The service is provided through a dependency so tests can override it with a fake.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field

from groundwork_api.service import AgentService, build_service

app = FastAPI(
    title="Groundwork API",
    version="0.1.0",
    summary="A LangGraph agent that answers AI-engineering questions, grounded in a knowledge base.",
)


# --- Schemas (also become the OpenAPI contract) ---


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["How does reciprocal rank fusion work?"])


class Citation(BaseModel):
    source: str
    heading: str


class AskResponse(BaseModel):
    question: str
    search_query: str
    answer: str
    citations: list[Citation]
    chunks_used: int


# --- Dependency: one AgentService for the process, overridable in tests ---


@lru_cache
def get_service() -> AgentService:
    return build_service()


# --- Routes ---


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, service: AgentService = Depends(get_service)) -> AskResponse:
    state = service.answer(req.question)
    return AskResponse(
        question=state["question"],
        search_query=state.get("search_query", ""),
        answer=state.get("answer", ""),
        citations=[Citation(**c) for c in state.get("citations", [])],
        chunks_used=len(state.get("chunks", [])),
    )
