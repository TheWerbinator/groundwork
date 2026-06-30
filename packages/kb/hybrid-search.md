---
title: Hybrid search
topic: hybrid-search
---

# Hybrid search

Hybrid search combines two retrieval methods that fail in different ways: dense vector search
and sparse keyword search. Each covers the other's blind spot, and fusing their rankings
retrieves more relevant chunks than either alone.

## Dense versus sparse

**Dense (vector) search** embeds query and chunks and compares them by cosine similarity. It
captures meaning, so it matches paraphrases and synonyms, but it can miss exact terms,
identifiers, error codes, or rare proper nouns that the embedding blurs together.

**Sparse (keyword) search**, classically BM25, scores documents by term frequency weighted by
how rare each term is across the corpus (inverse document frequency). BM25 adds two refinements
over plain TF-IDF: term-frequency saturation, so a word appearing twenty times is not worth
twenty times one occurrence, and document-length normalization, so long documents do not win
on length alone. It nails exact matches and rare tokens but understands no synonyms: a query
for "car" will not find a passage that only says "automobile."

_Source: [Elastic: Practical BM25 (Part 2)](https://www.elastic.co/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables) - plain-language breakdown of term frequency, IDF, saturation (k1), and length normalization (b)._

## Reciprocal Rank Fusion

The two methods produce two ranked lists with incomparable scores, so they cannot be merged
by adding scores. Reciprocal Rank Fusion (RRF) merges by rank instead. Each document gets a
score of the sum over both lists of 1 / (k + rank), where rank is its position in that list
and k is a small constant (commonly 60) that dampens the influence of top ranks. Documents
that rank well in either list rise to the top, and the constant keeps a single first-place
finish from dominating. RRF needs no score calibration; k is technically tunable but is
almost always left at 60, which is why it is the default fusion method in many production
systems.

_Source: [Cormack, Clarke & Buettcher (SIGIR 2009)](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) - the primary source for the RRF formula and the k=60 constant._

## Reranking after fusion

Fusion produces a candidate set, but the order is still approximate. A cross-encoder reranker,
itself a transformer model, reads each query-document pair together and scores relevance
directly, which is far more accurate than comparing independent embeddings. It is too slow to
run over the whole corpus, so it runs only over the fused candidate set as a final precision
step. Reranking is optional: RRF fusion alone is often shipped without it, and the reranker is
added when the extra precision is worth the latency. That makes reranking the latency-sensitive
hot path, which is a good reason to implement it as a fast dedicated service.

_Source: [Qdrant: Hybrid Search Revamped](https://qdrant.tech/articles/hybrid-search/) - cleanly separates fusion from reranking and explains why cross-encoders run only over candidates._

## Getting started

For a gentler on-ramp than the formulas, a worked dense-plus-sparse example with alpha
weighting shows the moving parts before the math.

_Source: [Pinecone Learn: Getting Started with Hybrid Search](https://www.pinecone.io/learn/hybrid-search-intro/) - problem-to-solution narrative with a worked example._

See also: rag, embeddings, evaluation.
