---
title: Retrieval-Augmented Generation
topic: rag
---

# Retrieval-Augmented Generation

Retrieval-Augmented Generation (RAG) grounds a language model's answer in documents
retrieved at query time instead of relying only on what the model memorized during training.
The pattern was introduced by Lewis et al. in 2020, pairing a generator with a non-parametric
memory (a searchable document index) so the model could pull in knowledge it was never trained
on. It has three working stages: ingest, retrieve, generate.

## Why RAG

A base model's knowledge is frozen at its training cutoff and it cannot cite a source. RAG
fixes both problems. At query time the system fetches the most relevant passages from a
corpus the operator controls, then asks the model to answer using only those passages. This
keeps answers current, lets the operator update knowledge by editing documents rather than
retraining, and makes every claim traceable to a source.

_Source: [Pinecone Learn: Retrieval-Augmented Generation](https://www.pinecone.io/learn/retrieval-augmented-generation/) - clear, motivation-first walkthrough of the whole flow. Primary source: [Lewis et al., 2020](https://arxiv.org/abs/2005.11401)._

## The pipeline

1. **Ingest.** Documents are split into chunks, each chunk is embedded into a vector, and the
   vectors are stored in a vector database alongside the original text and metadata.
2. **Retrieve.** The user's query is embedded with the same model and the store returns the
   nearest chunks. Hybrid retrieval also runs a keyword search and fuses the two rankings.
3. **Augment.** The retrieved chunks are assembled with the user's question into a single
   prompt. This prompt-assembly step is easy to overlook but it is where context formatting,
   ordering, and token budget are decided.
4. **Generate.** The model answers from the assembled context and is instructed to cite which
   chunk each claim came from.

Some references collapse augment and generate into one step. Naming augmentation separately
makes the prompt-construction decisions visible, which is where a lot of quality is won or
lost.

_Source: [Hugging Face Cookbook: Open-source RAG](https://huggingface.co/learn/cookbook/en/rag_zephyr_langchain) - a runnable notebook that builds each stage and shows answers with versus without retrieval._

## Grounding and citations

A grounded answer is one whose claims are supported by the retrieved context. Enforcing
grounding is a guardrail concern: the system can check that the answer cites at least one
retrieved chunk and reject or flag answers that introduce facts not present in the context.
This is the strongest single defense against hallucination in a RAG system, but it is not a
complete one. A model can still misread a correctly retrieved passage or over-extrapolate
beyond it, so grounding reduces hallucination rather than eliminating it.

_Source: [Anthropic: Introducing Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval) - rigorous explainer of retrieval quality and its measured effect on failure rates._

## Where RAG fails

Retrieval quality caps answer quality. If the right chunk is not retrieved, the model cannot
use it, so chunking strategy, embedding choice, hybrid search, and reranking all matter more
than prompt wording. Garbage retrieval produces confident, well-written, wrong answers.

Reranking deserves a specific mention because it is one of the highest-leverage levers. In
Anthropic's measurements, combining contextual embeddings with BM25 cut retrieval failures by
49%, and adding a reranking step on top pushed the reduction to 67%. A two-stage retrieve-then-
rerank pipeline is often the cheapest large quality win available.

_Source: [Anthropic: Introducing Contextual Retrieval](https://www.anthropic.com/engineering/contextual-retrieval) - reports the retrieve-then-rerank failure-rate reductions cited here._

See also: chunking, embeddings, hybrid-search, guardrails.
