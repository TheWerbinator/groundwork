"""Chroma vector store wrapper.

Defaults to a local on-disk PersistentClient so ingestion needs no running services. Set
CHROMA_HOST (e.g. http://localhost:8001) to target the Chroma server from docker-compose
instead. Embeddings are computed by our own Embedder and passed in explicitly, rather than
relying on Chroma's built-in embedding function, so the embedding choice is visible and
swappable.
"""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import chromadb

from ingestion.chunking import Chunk
from ingestion.config import Settings


@dataclass
class Retrieved:
    text: str
    metadata: dict
    distance: float


class ChromaStore:
    def __init__(self, settings: Settings) -> None:
        if settings.chroma_host:
            parsed = urlparse(settings.chroma_host)
            self._client = chromadb.HttpClient(
                host=parsed.hostname or "localhost",
                port=parsed.port or 8000,
            )
        else:
            settings.index_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(settings.index_path))

        # cosine space matches normalized embedding models like bge and text-embedding-3.
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return self._collection.count()

    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Idempotent load: a deterministic id per chunk means re-running ingest replaces
        rather than duplicates."""
        ids = [self._chunk_id(c) for c in chunks]
        self._collection.upsert(
            ids=ids,
            documents=[c.text for c in chunks],
            embeddings=embeddings,
            metadatas=[c.metadata for c in chunks],
        )

    def query(self, query_embedding: list[float], n_results: int = 5) -> list[Retrieved]:
        res = self._collection.query(query_embeddings=[query_embedding], n_results=n_results)
        out: list[Retrieved] = []
        docs = res["documents"][0]
        metas = res["metadatas"][0]
        dists = res["distances"][0]
        for text, meta, dist in zip(docs, metas, dists):
            out.append(Retrieved(text=text, metadata=meta or {}, distance=dist))
        return out

    @staticmethod
    def _chunk_id(chunk: Chunk) -> str:
        source = chunk.metadata.get("source", "doc")
        index = chunk.metadata.get("chunk_index", 0)
        return f"{source}:{index}"
