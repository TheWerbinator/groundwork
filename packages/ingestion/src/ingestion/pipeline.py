"""The ingest pipeline: read KB markdown -> chunk -> embed -> upsert into Chroma."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ingestion.chunking import Chunk, MarkdownChunker
from ingestion.config import Settings
from ingestion.embeddings import build_embedder
from ingestion.store import ChromaStore


@dataclass
class IngestReport:
    documents: int
    chunks: int
    embedder: str
    collection_count: int


def _parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    """Split a leading '---' YAML-ish frontmatter block from the body.

    Only simple `key: value` lines are read (our frontmatter is flat). A full YAML parser is
    avoided on purpose to keep the dependency surface small.
    """
    if not raw.startswith("---"):
        return {}, raw
    lines = raw.splitlines()
    if lines[0].strip() != "---":
        return {}, raw
    meta: dict[str, str] = {}
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            body = "\n".join(lines[i + 1 :]).lstrip("\n")
            return meta, body
        key, sep, value = lines[i].partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return {}, raw  # no closing fence; treat whole file as body


def load_documents(kb_path: Path) -> list[tuple[dict[str, str], str]]:
    docs: list[tuple[dict[str, str], str]] = []
    for path in sorted(kb_path.glob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        meta, body = _parse_frontmatter(path.read_text(encoding="utf-8"))
        meta = {**meta, "source": path.stem}
        meta.setdefault("title", path.stem)
        docs.append((meta, body))
    return docs


def chunk_documents(docs: list[tuple[dict[str, str], str]], settings: Settings) -> list[Chunk]:
    chunker = MarkdownChunker(chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)
    chunks: list[Chunk] = []
    for meta, body in docs:
        chunks.extend(chunker.split(body, dict(meta)))
    return chunks


def run_ingest(settings: Settings) -> IngestReport:
    docs = load_documents(settings.kb_path)
    chunks = chunk_documents(docs, settings)

    embedder = build_embedder(settings)
    embeddings = embedder.embed_documents([c.text for c in chunks])

    store = ChromaStore(settings)
    store.upsert(chunks, embeddings)

    return IngestReport(
        documents=len(docs),
        chunks=len(chunks),
        embedder=embedder.name,
        collection_count=store.count,
    )
