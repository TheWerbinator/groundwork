"""Chunking strategies.

The chunk is the unit of retrieval, so the splitter is one of the highest-leverage choices in
the pipeline (see packages/kb/chunking.md). Strategies are interchangeable behind the `Chunker`
protocol so a different strategy can be selected and re-measured without touching the rest of
the pipeline.

Sizes here are measured in characters. Characters are a coarse proxy for tokens but need no
tokenizer dependency and are deterministic, which keeps these functions easy to unit test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Chunk:
    """One retrievable unit: its text plus metadata used for filtering and citation."""

    text: str
    metadata: dict[str, str | int] = field(default_factory=dict)


class Chunker(Protocol):
    def split(self, text: str, doc_meta: dict[str, str | int]) -> list[Chunk]:
        """Split one document's text into chunks, carrying doc_meta onto each."""
        ...


def _merge_overlap(pieces: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Greedily pack pieces into chunks under chunk_size, with a trailing-char overlap
    carried from the end of one chunk into the start of the next."""
    chunks: list[str] = []
    current = ""
    for piece in pieces:
        if not current:
            current = piece
        elif len(current) + 1 + len(piece) <= chunk_size:
            current = f"{current} {piece}"
        else:
            chunks.append(current)
            tail = current[-overlap:] if overlap > 0 else ""
            current = f"{tail} {piece}".strip() if tail else piece
    if current:
        chunks.append(current)
    return chunks


def _recursive_split(text: str, separators: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Split on the coarsest separator that keeps pieces under chunk_size, recursing into any
    piece that is still too large, then pack the pieces back up to chunk_size with overlap."""
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    sep = separators[0] if separators else ""
    rest = separators[1:]

    if sep == "":
        # Hard fallback: slice oversized atomic text by character window with overlap.
        step = max(1, chunk_size - overlap)
        return [text[i : i + chunk_size] for i in range(0, len(text), step)]

    parts = [p for p in text.split(sep) if p.strip()]
    if len(parts) == 1:
        # Separator did not actually divide the text; drop to the next finer separator.
        return _recursive_split(text, rest, chunk_size, overlap)

    pieces: list[str] = []
    for part in parts:
        if len(part) <= chunk_size:
            pieces.append(part.strip())
        else:
            pieces.extend(_recursive_split(part, rest, chunk_size, overlap))
    return _merge_overlap(pieces, chunk_size, overlap)


@dataclass
class RecursiveChunker:
    """Split on a coarse-to-fine separator list (paragraph, line, sentence, space), keeping
    natural boundaries while guaranteeing a maximum size."""

    chunk_size: int = 800
    overlap: int = 120
    separators: tuple[str, ...] = ("\n\n", "\n", ". ", " ", "")

    def split(self, text: str, doc_meta: dict[str, str | int]) -> list[Chunk]:
        bodies = _recursive_split(text, list(self.separators), self.chunk_size, self.overlap)
        return [
            Chunk(text=body, metadata={**doc_meta, "chunk_index": i})
            for i, body in enumerate(bodies)
        ]


def _split_markdown_sections(text: str) -> list[tuple[str, str]]:
    """Split Markdown into (heading_path, body) sections on ATX headings (#..######).

    The heading path is the breadcrumb of enclosing headings, e.g. "Hybrid search > Dense
    versus sparse", attached so each chunk knows the section it came from.
    """
    sections: list[tuple[str, str]] = []
    stack: list[tuple[int, str]] = []  # (level, heading text)
    buf: list[str] = []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body:
            path = " > ".join(h for _, h in stack)
            sections.append((path, body))
        buf.clear()

    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            hashes = len(stripped) - len(stripped.lstrip("#"))
            if 1 <= hashes <= 6 and stripped[hashes : hashes + 1] in (" ", ""):
                flush()
                heading = stripped[hashes:].strip()
                while stack and stack[-1][0] >= hashes:
                    stack.pop()
                stack.append((hashes, heading))
                continue
        buf.append(line)
    flush()
    return sections


@dataclass
class MarkdownChunker:
    """Structure-aware default: split on Markdown headings, keep each section together, and
    fall back to recursive splitting for any section larger than chunk_size. The heading path
    is stored on each chunk for filtering and citation."""

    chunk_size: int = 800
    overlap: int = 120

    def split(self, text: str, doc_meta: dict[str, str | int]) -> list[Chunk]:
        recursive = RecursiveChunker(self.chunk_size, self.overlap)
        chunks: list[Chunk] = []
        for path, body in _split_markdown_sections(text):
            section_meta = {**doc_meta}
            if path:
                section_meta["heading"] = path
            if len(body) <= self.chunk_size:
                bodies = [body]
            else:
                bodies = [c.text for c in recursive.split(body, {})]
            for body_text in bodies:
                meta = {**section_meta, "chunk_index": len(chunks)}
                chunks.append(Chunk(text=body_text, metadata=meta))
        return chunks
