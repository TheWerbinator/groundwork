"""Embedders.

Two interchangeable implementations behind one protocol: a local fastembed model (default,
free, offline) and a hosted OpenAI model (swap in via config). Queries and passages are
embedded through distinct methods so a model that wants an instruction prefix on queries can
apply it without the rest of the pipeline knowing (see packages/kb/embeddings.md).
"""

from __future__ import annotations

from typing import Protocol

from ingestion.config import Settings

# bge-small-en-v1.5 is trained to retrieve long passages from short queries when the query
# carries this instruction. Passages are embedded as-is.
_BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class Embedder(Protocol):
    @property
    def name(self) -> str: ...

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class FastEmbedEmbedder:
    """Local ONNX embeddings via fastembed. No API key, runs offline after the one-time
    model download."""

    def __init__(self, model_name: str) -> None:
        # Imported lazily so the package imports cleanly even before deps are installed.
        from fastembed import TextEmbedding

        self._model_name = model_name
        self._model = TextEmbedding(model_name=model_name)
        self._is_bge = "bge" in model_name.lower()

    @property
    def name(self) -> str:
        return f"fastembed:{self._model_name}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # fastembed returns a generator of numpy arrays.
        return [vec.tolist() for vec in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        if self._is_bge:
            text = _BGE_QUERY_INSTRUCTION + text
        return next(iter(self._model.embed([text]))).tolist()


class OpenAIEmbedder:
    """Hosted embeddings via the OpenAI API. Needs OPENAI_API_KEY."""

    def __init__(self, model_name: str, api_key: str) -> None:
        if not api_key:
            raise ValueError(
                "EMBEDDING_PROVIDER=openai requires OPENAI_API_KEY. "
                "Set it in .env or switch EMBEDDING_PROVIDER back to fastembed."
            )
        from openai import OpenAI  # optional dependency, install with: uv sync --extra openai

        self._model_name = model_name
        self._client = OpenAI(api_key=api_key)

    @property
    def name(self) -> str:
        return f"openai:{self._model_name}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(model=self._model_name, input=texts)
        return [item.embedding for item in resp.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def build_embedder(settings: Settings) -> Embedder:
    """Construct the embedder named by settings.embedding_provider."""
    provider = settings.embedding_provider.lower()
    if provider == "fastembed":
        return FastEmbedEmbedder(settings.fastembed_model)
    if provider == "openai":
        return OpenAIEmbedder(settings.openai_embedding_model, settings.openai_api_key)
    raise ValueError(
        f"Unknown EMBEDDING_PROVIDER {provider!r}. Expected 'fastembed' or 'openai'."
    )
