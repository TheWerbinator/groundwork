# Groundwork

**An agentic AI-engineering assistant that answers grounded questions from a curated
knowledge base, and is itself a worked, traced, evaluated example of every technique it
explains.**

The corpus is *about* the same stack the app is built from (LangGraph, MCP, RAG, evals,
guardrails, observability). Reading the answers teaches the architecture. The repo is a
teaching artifact first, a product second: every component is meant to be pointed at in an
interview and explained on its own.

## Goals and constraints

- **Simple and teachable.** One cohesive product, one mental model. Each capability maps to
  one visible, isolated piece.
- **Local-first.** Everything runs via Docker Compose. No always-on cloud, no live URL for
  v1. AWS / k8s are shipped as IaC + docs, not a running bill.
- **Defensible.** Every tech choice is explainable in an interview. No buzzword padding.
- **Build one, document the rest.** For each "compare to X" item in the brief, build a single
  real implementation and document the alternatives in `docs/`.

## Stack

- **Backend:** Python + FastAPI (REST + OpenAPI typed client).
- **Frontend:** Next.js + TypeScript (chat + Human-in-the-Loop review).
- **Agent framework:** LangGraph.
- **Vector store:** Chroma (local) + BM25 hybrid + reciprocal-rank fusion.
- **High-perf service:** Rust rerank microservice (ONNX cross-encoder via `ort`).
- **Models (3-way eval):** Claude (default strong model) + OpenAI (GPT) + local Ollama
  open-source model.
- **Observability:** OpenTelemetry traces to local Jaeger.
- **Glue:** Docker Compose.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Next.js UI (TS)  - chat + Human-in-the-Loop review panel    │
└───────────────┬─────────────────────────────────────────────┘
                │ REST (OpenAPI typed client)
┌───────────────▼─────────────────────────────────────────────┐
│  FastAPI backend (Python)                                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ LangGraph agent: planner->retriever->drafter->critic   │ │
│  │ loop with self-reflection                              │ │
│  └───┬───────────────┬───────────────┬────────────────────┘ │
│      │ MCP client     │ guardrails    │ cost/cache meter      │
│  ┌───▼───────┐   ┌────▼──────┐   ┌────▼──────┐               │
│  │ MCP server│   │ Chroma +  │   │ semantic  │               │
│  │ (KB+tools)│   │ BM25      │   │ cache     │               │
│  └───────────┘   │ hybrid    │   └───────────┘               │
│                  └────┬──────┘                               │
│                       │ rerank (hot path)                    │
│                  ┌────▼───────────┐                          │
│                  │ Rust rerank svc │ (REST, ONNX cross-enc)  │
│                  └────────────────┘                          │
└──────────────────────────────────────────────────────────────┘
   │ OpenTelemetry traces -> Jaeger (local)
   │ Eval harness (offline): Claude vs GPT vs Ollama on golden set
   │ infra/: Dockerfiles, k8s manifests, AWS IaC (Terraform) - docs, not always-on
```

## Component to capability map

| Component | Teaches | Build vs Document |
|---|---|---|
| LangGraph state graph (planner / retriever / drafter / critic + reflection) | multi-agent, autonomous planning, self-reflection | **Build**. AutoGen / CrewAI = doc comparison |
| Chroma + BM25 hybrid + reciprocal-rank fusion | RAG, vector DB, hybrid search | **Build** on Chroma. Pinecone / Weaviate / Milvus = doc comparison |
| Ingestion pipeline (chunking strategies, embedding models, swappable) | embeddings, chunking, unstructured data | **Build** |
| MCP server exposing KB-search + 1-2 internal tools | Model Context Protocol | **Build** (real MCP server + agent as MCP client) |
| Rust rerank microservice (ONNX cross-encoder via `ort`) | high-perf inference, polyglot | **Build** small |
| Eval harness (golden Q&A set, scored offline) | foundation-model eval, cost / latency / accuracy | **Build** 3-way |
| Guardrails (input: PII / injection; output: grounding / citation enforcement) | safety, privacy, compliance, bias | **Build** deterministic checks |
| HITL review panel | human-in-the-loop | **Build** |
| OTel -> Jaeger | tracing reasoning chains | **Build** |
| Cost meter + prompt cache + semantic cache | token / cost optimization | **Build** |
| `infra/` Docker + k8s + Terraform(AWS) + monitoring docs | cloud-native, MLOps / LLMOps, drift / hallucination monitoring | **Build IaC + docs**, run locally; AWS not always-on. Azure / GCP = doc comparison |

## Repo layout

```
groundwork/
  apps/
    api/        FastAPI + LangGraph agent + guardrails + eval
    web/        Next.js HITL UI
    rerank/     Rust ONNX rerank service
    mcp/        MCP server (KB + tools)
  packages/
    ingestion/  chunking + embeddings pipeline
    kb/         the AI-engineering corpus (markdown sources)
  eval/         golden set + harness + reports
  infra/        docker-compose, k8s, terraform, monitoring dashboards
  docs/         per-tech teaching pages + alternatives comparisons
  README.md     architecture + "what each piece teaches" index
```

## Phase plan

Each phase is a working, committed, documented slice. Each ends with:
verify -> PROGRESS.md -> DECISIONS.md -> commit title + description.

0. **Bootstrap** - repo, `.gitignore` (`.env*` guarded), Docker Compose skeleton, README
   index, PROGRESS.md + DECISIONS.md. *(this phase)*
1. **Corpus + ingestion** - curate the AI-eng KB markdown; chunking + embeddings pipeline
   into Chroma.
2. **Hybrid retrieval** - BM25 + vector + rank fusion. Rust rerank stubbed (real in phase 7).
3. **Agent v1 (LangGraph)** - planner -> retriever -> drafter, grounded answers + citations,
   REST endpoint.
4. **Guardrails** - input PII / injection; output grounding / citation enforcement.
5. **Self-reflection + critic node** - agent critiques and retries weak answers.
6. **MCP** - stand up MCP server; agent calls KB + tools through it.
7. **Rust rerank service** - ONNX cross-encoder, wired into the phase-2 hot path.
8. **HITL UI (Next.js)** - chat + step approve / edit / reject.
9. **Observability** - OTel spans across the chain -> Jaeger; cost meter + semantic cache.
10. **Eval harness** - golden set; 3-way Claude / GPT / Ollama; cost / latency / accuracy
    report.
11. **Infra + docs** - Dockerfiles, k8s manifests, Terraform(AWS), monitoring / drift docs,
    alternatives comparison docs, polish READMEs.

## Out of scope for v1

- Always-on cloud deployment / public live URL.
- Multi-tenant auth (this is a single-user teaching demo).
- Fine-tuning (open-source fine-tuned models are documented, not trained here).
