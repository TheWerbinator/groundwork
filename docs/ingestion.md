# Ingestion: turning documents into retrievable chunks

> A guided walkthrough of the code in [`packages/ingestion`](../packages/ingestion). This page
> teaches how *our* pipeline works. For the concepts themselves, follow the links into the
> knowledge base ([chunking](../packages/kb/chunking.md), [embeddings](../packages/kb/embeddings.md)).

## What you'll learn

- The four jobs every RAG ingestion pipeline does, and where each lives in our code.
- Why chunking is the highest-leverage step, and how the Markdown-aware chunker works.
- How an embedding turns text into a vector, and why we made the embedder swappable.
- How chunks land in Chroma so they can be searched, and why re-ingesting is safe.

## The pipeline at a glance

Ingestion has four stages. Our code keeps them as separate, readable functions:

```
load  ->  chunk  ->  embed  ->  store
 |         |          |          |
 |         |          |          ChromaStore.upsert  (store.py)
 |         |          build_embedder().embed_documents (embeddings.py)
 |         MarkdownChunker.split  (chunking.py)
 load_documents  (pipeline.py)
```

[`pipeline.py`](../packages/ingestion/src/ingestion/pipeline.py) is the conductor; read
`run_ingest` first and the whole flow fits on one screen.

## 1. Load: documents in, metadata attached

`load_documents` reads each `*.md` in the [knowledge base](../packages/kb), splits off the
`---` frontmatter, and attaches `source` (the filename) and `title`. That `source` becomes the
chunk's citation later, so it is set here at the very start.

We parse frontmatter by hand (`_parse_frontmatter`) instead of pulling in a YAML library,
because our frontmatter is flat `key: value` lines. One fewer dependency, and the parser is a
dozen lines you can read.

## 2. Chunk: the most important step

The chunk is the unit of retrieval. Too big and the relevant sentence drowns in noise; too
small and it loses context. See [chunking.md](../packages/kb/chunking.md) for the why; here is
the how.

[`chunking.py`](../packages/ingestion/src/ingestion/chunking.py) defines a `Chunker` protocol
(an interface) with two implementations, so the strategy is swappable:

- **`MarkdownChunker`** (default). `_split_markdown_sections` walks the document heading by
  heading, keeping a `stack` of the current heading path. Each section becomes a chunk tagged
  with its breadcrumb, for example `Hybrid search > Reciprocal Rank Fusion`. That breadcrumb is
  what you see in every retrieval result, and it is how an answer can cite *which section* a
  fact came from. If a section is larger than `chunk_size`, it falls back to:
- **`RecursiveChunker`**. It tries separators coarse-to-fine (`\n\n`, then `\n`, then `. `,
  then ` `) and splits on the coarsest one that keeps chunks under the limit, recursing into
  any piece still too big, then packs the pieces back up with a little overlap so a sentence
  cut at a boundary still appears whole in a neighbor.

Sizes are measured in **characters**, not tokens, on purpose: no tokenizer dependency, and the
splitting is deterministic, which is what lets the unit tests in
[`tests/test_chunking.py`](../packages/ingestion/tests/test_chunking.py) assert exact behavior.

## 3. Embed: text becomes a vector

An embedding model maps text to a fixed-length vector so similar meanings land near each other
(see [embeddings.md](../packages/kb/embeddings.md)).
[`embeddings.py`](../packages/ingestion/src/ingestion/embeddings.py) defines an `Embedder`
protocol with two implementations:

- **`FastEmbedEmbedder`** (default) runs `BAAI/bge-small-en-v1.5` locally. No API key, works
  offline. Note `embed_query` prepends the bge query instruction, while `embed_documents` does
  not: this is the query/passage asymmetry the corpus doc describes, encoded in code.
- **`OpenAIEmbedder`** is the hosted swap, selected by `EMBEDDING_PROVIDER=openai`.

`build_embedder(settings)` is the factory that returns whichever the config asks for. The rest
of the pipeline never knows which embedder it got, which is the point of the protocol.

## 4. Store: into Chroma, idempotently

[`store.py`](../packages/ingestion/src/ingestion/store.py) wraps Chroma. Two design points
worth understanding:

- **We compute embeddings ourselves and pass them in**, rather than letting Chroma embed for
  us. This keeps the embedding choice visible and swappable instead of hidden inside the store.
- **Deterministic ids** (`source:chunk_index`) mean `upsert` *replaces* a chunk on re-ingest
  instead of duplicating it. That is why running `ingestion ingest` twice leaves the count
  unchanged. `get_all()` (added for Phase 2) returns every chunk so the BM25 index can be built
  over the same corpus.

The collection is created with `hnsw:space = cosine`, matching the normalized vectors bge and
text-embedding-3 produce.

## Run it yourself

```bash
cd packages/ingestion
uv sync
uv run ingestion ingest
uv run ingestion query "how does reciprocal rank fusion work?"
```

What to watch:

- The ingest line reports `8 docs -> N chunks`. That `N` is set by your chunk size.
- Each query result shows `source (heading path)` and a `cosine_distance`. Smaller distance =
  closer match. Notice the top hit's heading path points at the exact section.

## Try this

1. **Change the chunk size.** Set `chunk_size` smaller (edit the default in
   [`config.py`](../packages/ingestion/src/ingestion/config.py), or export `CHUNK_SIZE`), then
   re-ingest. Watch the chunk count rise and the retrieved snippets get shorter and more
   precise. This is the precision-versus-context tradeoff, live.
2. **Swap the embedder.** Set `EMBEDDING_PROVIDER=openai` (with `OPENAI_API_KEY`) and re-ingest.
   Same pipeline, different vectors. Compare retrieval on a tricky paraphrase.
3. **Add a doc.** Drop a new `*.md` into [`packages/kb`](../packages/kb) with frontmatter,
   re-ingest, and query it. Nothing else changes.

## Design choices

The reasoning behind each decision (local-first defaults, Markdown chunker, deterministic ids,
computing embeddings ourselves) is recorded under "Phase 1 decisions" in
[DECISIONS.md](../DECISIONS.md).

## Where it goes next

These chunks are the input to search. Continue with
[retrieval.md](retrieval.md): how dense and sparse retrieval rank them and how fusion combines
the two.
