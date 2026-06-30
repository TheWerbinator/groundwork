---
title: Chunking strategies
topic: chunking
---

# Chunking strategies

Chunking is the step that splits a document into the units that get embedded and retrieved.
It is the highest-leverage and most underrated decision in a RAG pipeline: the chunk is the
unit of retrieval, so a chunk that is too big buries the relevant sentence in noise and a
chunk that is too small loses the context needed to understand it.

## Fixed-size chunking

The simplest strategy splits text every N characters or tokens, often with an overlap of
10-20% so a sentence cut at a boundary still appears whole in a neighboring chunk. It is fast
and predictable but blind to structure: it will happily cut a code block or a table in half.

One subtlety: characters and tokens are not the same unit. Embedding models have a maximum
input measured in tokens, and one token averages about four characters of English, so a
splitter that counts characters can overshoot the model's token limit. Splitters usually let
you supply a length function so the size cap is enforced in the same unit the model uses.

_Source: [Pinecone Learn: Chunking Strategies](https://www.pinecone.io/learn/chunking-strategies/) - vendor-neutral conceptual tour from fixed-size onward._

## Recursive chunking

Recursive chunking tries a list of separators in order, from coarse to fine: paragraph
breaks, then lines, then sentences, then words. It splits on the coarsest separator that keeps
chunks under the size limit, recursing into any piece that is still too large. This respects
natural boundaries far better than fixed-size while still guaranteeing a maximum size, and it
is the sensible default for general prose.

_Source: [LangChain: Recursive text splitter](https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter) - authoritative reference for the coarse-to-fine separator list and the length-function knob._

## Structure-aware chunking

For Markdown, HTML, or code, the best splitters use the document's own structure. A
Markdown-aware splitter breaks on headings and keeps each section together, attaching the
heading path as metadata so a chunk knows which section it came from. This metadata is
valuable for both retrieval filtering and citation.

## Semantic and late chunking

Two newer strategies go beyond separators. **Semantic chunking** embeds sentences and places a
boundary wherever the meaning shifts (a large drop in similarity between adjacent sentences),
so each chunk is topically coherent. It raises recall but is much slower because it embeds
during splitting. **Late chunking** inverts the order: embed the whole document first with a
long-context model so every token attends to the full text, then partition the resulting token
embeddings into chunks. This preserves pronouns and cross-references that early splitting would
strand. Both are worth knowing, though recursive splitting often wins end-to-end accuracy in
practice because coherent, predictable chunks are easy for the model to use.

_Source: [Weaviate: Chunking Strategies for RAG](https://weaviate.io/blog/chunking-strategies-for-rag) - covers every strategy with code and animated visualizations of how each splits text._

## Choosing size and overlap

There is no universal best size. Smaller chunks (around 200-400 tokens) give precise
retrieval and suit fact lookup; larger chunks (800-1000 tokens) preserve more context and
suit reasoning over a passage. Overlap reduces boundary loss at the cost of duplicated
storage and some redundant retrieval. The honest answer is to measure: run the eval harness
with different chunkers and compare retrieval hit rate.

_Source: [Greg Kamradt: 5 Levels of Text Splitting](https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/tutorials/LevelsOfTextSplitting/5_Levels_Of_Text_Splitting.ipynb) - hands-on notebook progressing from fixed to recursive to semantic to agentic splitting._

## A swappable interface

Because the right choice is empirical, the chunker should be an interface with
interchangeable implementations, selected by configuration, so the strategy can be changed
and re-measured without touching the rest of the pipeline.

See also: embeddings, rag, evaluation.
