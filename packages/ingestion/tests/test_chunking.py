"""Chunking tests. Pure functions, no network or model download."""

from __future__ import annotations

from ingestion.chunking import MarkdownChunker, RecursiveChunker, _split_markdown_sections


def test_recursive_respects_max_size():
    text = "word " * 1000  # ~5000 chars, no paragraph/sentence breaks
    chunks = RecursiveChunker(chunk_size=200, overlap=20).split(text, {})
    assert chunks, "expected at least one chunk"
    # Allow a small slack for the overlap tail glued onto the front of each chunk.
    assert all(len(c.text) <= 200 + 20 for c in chunks)


def test_recursive_overlap_carries_context():
    parts = [f"Sentence number {i} has its own content." for i in range(40)]
    text = " ".join(parts)
    chunks = RecursiveChunker(chunk_size=120, overlap=40).split(text, {})
    assert len(chunks) > 1
    # With overlap, consecutive chunks should share some trailing/leading text.
    shared = any(
        chunks[i].text[-20:].strip() and chunks[i].text[-20:].strip() in chunks[i + 1].text
        for i in range(len(chunks) - 1)
    )
    assert shared


def test_recursive_carries_doc_meta_and_index():
    chunks = RecursiveChunker(chunk_size=50, overlap=10).split(
        "alpha. " * 50, {"source": "doc", "title": "Doc"}
    )
    assert all(c.metadata["source"] == "doc" for c in chunks)
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))


def test_markdown_section_split_tracks_heading_path():
    md = (
        "# Title\n\nintro body\n\n"
        "## Section A\n\nbody a\n\n"
        "### Sub A1\n\nbody a1\n\n"
        "## Section B\n\nbody b\n"
    )
    sections = _split_markdown_sections(md)
    paths = [p for p, _ in sections]
    assert "Title" in paths
    assert "Title > Section A" in paths
    assert "Title > Section A > Sub A1" in paths
    assert "Title > Section B" in paths  # B pops A1 and A off the stack


def test_markdown_chunker_attaches_heading_metadata():
    md = "# Doc\n\n## Topic\n\nsome content about retrieval\n"
    chunks = MarkdownChunker(chunk_size=800, overlap=100).split(md, {"source": "d"})
    assert chunks
    assert any("Topic" in str(c.metadata.get("heading", "")) for c in chunks)
    assert all(c.metadata["source"] == "d" for c in chunks)


def test_markdown_large_section_falls_back_to_recursive():
    big = "para. " * 400  # one big section, ~2400 chars
    md = f"# Doc\n\n## Big\n\n{big}\n"
    chunks = MarkdownChunker(chunk_size=300, overlap=40).split(md, {"source": "d"})
    assert len(chunks) > 1
    assert all(len(c.text) <= 300 + 40 for c in chunks)
    # chunk_index is unique and contiguous across the whole document
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))
