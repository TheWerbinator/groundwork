---
title: Embedding models
topic: embeddings
---

# Embedding models

An embedding model maps a piece of text to a fixed-length vector of floating-point numbers so
that texts with similar meaning land near each other in vector space. RAG retrieval is built
on this: embed the chunks once at ingest time, embed the query at search time, and return the
chunks whose vectors are closest to the query's.

## Similarity

Closeness is usually measured by cosine similarity, the cosine of the angle between two
vectors, which ignores magnitude and compares direction. Many models are trained so that
cosine similarity tracks semantic similarity directly, which is why normalized vectors and
cosine distance are the common default in vector stores. When vectors are normalized to unit
length, cosine similarity and dot product give the same ranking. Hosted models often return
already-normalized vectors; a local model may need an explicit normalize flag, so it is worth
checking rather than assuming.

_Source: [Cohere LLM University: Text Embeddings](https://cohere.com/llmu/text-embeddings) - intuition-first lesson that builds the mental model before any math._

## Dimensions and tradeoffs

Each model emits vectors of a fixed dimension, for example 384 for BAAI/bge-small-en-v1.5 or
1536 for OpenAI text-embedding-3-small. Higher dimensions can capture more nuance but cost
more storage and compute per query. Some newer models are trained with Matryoshka
representation learning, where the most important information is packed into the leading
dimensions, so a 1536-dimension vector can be truncated to 512 or 256 and still work. OpenAI's
text-embedding-3 models expose this directly through a `dimensions` parameter, which turns the
storage-versus-quality tradeoff into an explicit dial.

_Source: [OpenAI: Embeddings guide](https://platform.openai.com/docs/guides/embeddings) - documents the `dimensions` parameter and default normalization._

## Choosing a model

Because models vary in quality, speed, and dimension, choosing one is empirical. The Massive
Text Embedding Benchmark (MTEB) scores models across dozens of retrieval, clustering, and
classification tasks, and its leaderboard is the standard starting point. A small local model
like bge-small scores well enough on retrieval for many tasks while staying cheap and offline,
which is why "good enough and local" is often the right call rather than the top of the board.

_Source: [Hugging Face: MTEB blog](https://huggingface.co/blog/mteb) - explains how embedding models are benchmarked and how to read the speed-versus-quality curve._

## Query and passage asymmetry

Some models are trained with separate roles for queries and passages and expect a short
instruction prefix, such as prefixing a search query differently from a stored passage.
bge-small, for instance, prepends "Represent this sentence for searching relevant passages:"
to queries only, leaving passages unprefixed (v1.5 made this optional, with a smaller penalty
when omitted). Using the prescribed prefixes measurably improves retrieval, so the embedding
code should encode this asymmetry rather than treating queries and documents identically.

_Source: [Sentence-Transformers: Semantic Search](https://sbert.net/examples/applications/semantic-search/README.html) - teaches the symmetric versus asymmetric (query versus passage) distinction with runnable examples._

## Local versus hosted

A hosted embedding API (OpenAI, Cohere, Voyage) offers strong quality with zero local setup
but adds latency, cost, and a network dependency on every ingest and query. A local model
(via fastembed or sentence-transformers) runs on the machine, is free per call, and keeps
data in-house, at the cost of managing the model download and some quality gap. The embedder
should be swappable so this tradeoff can be revisited per deployment.

_Source: [BAAI/bge-small-en-v1.5 model card](https://huggingface.co/BAAI/bge-small-en-v1.5) - primary source for the 384-dim size, query instruction, and normalization guidance._

See also: chunking, rag, hybrid-search.
