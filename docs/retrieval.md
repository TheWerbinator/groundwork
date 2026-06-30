# Hybrid retrieval: dense + sparse + fusion

> A guided walkthrough of the code in [`packages/retrieval`](../packages/retrieval). For the
> concept, read [hybrid-search.md](../packages/kb/hybrid-search.md) in the knowledge base; this
> page shows how our code implements it.

## What you'll learn

- Why two retrieval methods beat one, and how each fails differently.
- How BM25 keyword scoring works in our code, over the same chunks the vectors came from.
- Reciprocal Rank Fusion, worked through with real numbers.
- Why reranking is a seam today and a Rust service in Phase 7.

## The shape of it

```
query
  |
  +--> dense  (vector search over embeddings)   --> ranked ids
  |                                                     \
  +--> sparse (BM25 keyword search)             --> ranked ids
                                                        |
                              reciprocal_rank_fusion (merge by rank)
                                                        |
                                   reranker (reorder candidates, truncate)
                                                        |
                                                  top_k results
```

[`hybrid.py`](../packages/retrieval/src/retrieval/hybrid.py)'s `HybridRetriever.retrieve` is
the conductor. Read it top to bottom and the diagram above is the function body.

## Dense and sparse: two ways to fail

- **Dense** (`vector_search`) embeds the query and asks Chroma for the nearest chunks. It
  matches *meaning*, so a query for "car" finds a passage about "automobiles", but it can blur
  rare exact tokens like an error code or `Streamable HTTP`.
- **Sparse** (`sparse_search`, backed by [`bm25.py`](../packages/retrieval/src/retrieval/bm25.py))
  scores by keyword overlap. It nails exact and rare terms but understands no synonyms.

They cover each other's blind spots, which is the whole argument for hybrid search.

### How BM25 works in our code

`BM25Index` is built in memory from `store.get_all()`, so the keyword index covers exactly the
chunks the vector index holds. `tokenize` lowercases and splits on non-alphanumeric runs, a
deterministic function the tests pin down. `search` scores every chunk against the query tokens
with `rank-bm25` and returns the top ids. BM25 weights a term by how often it appears in a
chunk and how rare it is across the corpus, with saturation and length normalization (the
details are in the corpus doc).

The corpus is small, so rebuilding this in memory is simple and fast. A large deployment would
persist a sparse index instead; that tradeoff is noted in the decisions.

## Fusion: merging two rankings that can't be compared

A cosine distance and a BM25 score live on different scales, so you cannot add them. RRF sidesteps
this by merging on **rank**, not score. From
[`fusion.py`](../packages/retrieval/src/retrieval/fusion.py):

```
score(doc) = sum over each list of  1 / (k + rank)      # rank is 1-based, k = 60
```

Worked example. Two lists:

```
dense  = [A, C]      # A is rank 1, C is rank 2
sparse = [B, C]      # B is rank 1, C is rank 2
```

With k = 60:

```
A = 1/(60+1)                 = 0.0164      (only in the dense list)
B = 1/(60+1)                 = 0.0164      (only in the sparse list)
C = 1/(60+2) + 1/(60+2)      = 0.0323      (in BOTH lists)
```

C wins, even though it was never ranked first, because it showed up in *both* legs. That is the
property to internalize: agreement across methods is what fusion rewards. The constant `k`
(60 by convention, from Cormack et al. 2009) controls how sharply rank-1 is favored; a smaller
`k` makes the top rank dominate more. The unit tests in
[`test_fusion.py`](../packages/retrieval/tests/test_fusion.py) lock in exactly these numbers.

We fuse on the chunk's `source:index` id, the same deterministic id ingestion assigned, so the
two lists merge on a stable key with no extra bookkeeping.

## Reranking: a seam for now

Fusion gives an approximate order. A cross-encoder reranker reads each query-document pair
together and scores relevance directly, which is more accurate but too slow to run over the
whole corpus, so it runs only over the fused candidates.

[`rerank.py`](../packages/retrieval/src/retrieval/rerank.py) defines a `Reranker` protocol with
a `NoOpReranker` that just keeps the fused order and truncates to `top_k`. The whole pipeline is
already wired against the interface, so the Phase 7 Rust cross-encoder drops in by swapping the
implementation, with no change to `HybridRetriever`.

## Run it yourself

```bash
cd packages/retrieval
uv sync
uv run retrieval search "what is the k constant in RRF and where did 60 come from?"
```

The command prints three lists for the same query: dense, sparse, and the fused hybrid. Read
them together:

- Where dense and sparse **disagree**, you see each method's bias.
- Where they **agree**, fusion pushes that chunk to the top with a higher `rrf` score.

## Try this

1. **Rare-token query.** Search `Streamable HTTP transport stdio`. Both legs should agree on
   the MCP Transports section, because the exact tokens are distinctive. Now search a paraphrase
   like `how do MCP servers talk over a network` and watch dense carry more of the weight.
2. **Turn the fusion knob.** Lower `rrf_k` (in [`config.py`](../packages/ingestion/src/ingestion/config.py))
   and re-run. Top-ranked agreements get even stronger relative to single-list hits.
3. **Widen or narrow the funnel.** Change `candidate_pool` (how many each leg contributes) and
   `top_k` (how many survive) and see how the final list shifts.

## Design choices

The reasoning (separate read-path package, in-memory BM25, RRF over score combination, the
reranker seam) is under "Phase 2 decisions" in [DECISIONS.md](../DECISIONS.md).

## Where it goes next

Retrieval feeds the agent. Continue with [agents.md](agents.md): how the LangGraph agent plans
a query, calls this retriever, drafts a grounded answer, and critiques itself.
