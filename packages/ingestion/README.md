# packages/ingestion

The ingestion pipeline: read the [knowledge base](../kb) markdown, chunk it, embed the
chunks, and load them into Chroma. Shared by the agent and the eval harness.

Pipeline stages, each a swappable piece (see [packages/kb/chunking.md](../kb/chunking.md) and
[embeddings.md](../kb/embeddings.md) for the concepts):

1. **Load** - read `*.md`, split off simple `---` frontmatter, attach `source` + `title`.
2. **Chunk** - `MarkdownChunker` splits on headings and keeps each section together, storing
   the heading path on every chunk for citation; oversized sections fall back to a recursive
   character splitter. `RecursiveChunker` is the structure-agnostic alternative.
3. **Embed** - `FastEmbedEmbedder` (local `BAAI/bge-small-en-v1.5`, default, no key) or
   `OpenAIEmbedder` (hosted, `--extra openai`), chosen by `EMBEDDING_PROVIDER`.
4. **Store** - `ChromaStore` upserts with deterministic ids (re-ingest replaces, never
   duplicates). Local on-disk `PersistentClient` by default; set `CHROMA_HOST` to use a
   Chroma server.

## Usage

```bash
cd packages/ingestion
uv sync                     # installs deps; add --extra openai for hosted embeddings
uv run ingestion ingest     # chunk + embed + load the KB
uv run ingestion query "how does reciprocal rank fusion work?"
uv run pytest               # chunking unit tests (no network)
```

Configuration comes from the repo-root `.env` (see [`.env.example`](../../.env.example)).
Local defaults run with zero API keys; the on-disk index lives at `INDEX_PATH`
(`data/index`, gitignored).

**Learn how it works:** [docs/ingestion.md](../../docs/ingestion.md) is a guided walkthrough of
this code (concept -> our code -> run it -> exercises).

**Built in:** Phase 1. Retrieval (BM25 + fusion + rerank) builds on this in Phase 2.
