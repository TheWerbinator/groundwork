# Groundwork

> An agentic AI-engineering assistant that answers grounded questions from a curated
> knowledge base, and is itself a worked, traced, evaluated example of every technique it
> explains.

The knowledge base is *about* the same stack Groundwork is built from: LangGraph agents,
hybrid RAG, MCP, model evaluation, guardrails, and observability. Ask it "how does
reciprocal-rank fusion work?" and the grounded answer is describing the very retrieval step
that produced it. The repo is a teaching artifact: each component stands alone and is meant
to be explained on its own.

**Local-first.** The whole stack runs via Docker Compose. No cloud account required.

## What each piece teaches

| Capability | Lives in | Concept |
|---|---|---|
| Multi-agent planning + self-reflection | [apps/api](apps/api) (LangGraph) | autonomous planning, tool selection, critic loop |
| Hybrid RAG | [apps/api](apps/api) + [packages/ingestion](packages/ingestion) | vector + BM25 + reciprocal-rank fusion |
| Chunking + embeddings | [packages/ingestion](packages/ingestion) | unstructured data -> retrievable chunks |
| Model Context Protocol | [apps/mcp](apps/mcp) | exposing tools + data to agents over MCP |
| High-perf reranking | [apps/rerank](apps/rerank) (Rust) | ONNX cross-encoder on the RAG hot path |
| Foundation-model eval | [eval](eval) | Claude vs GPT vs Ollama: cost / latency / accuracy |
| Guardrails + safety | [apps/api](apps/api) | PII / injection / grounding / citation enforcement |
| Human-in-the-Loop | [apps/web](apps/web) (Next.js) | approve / edit / reject agent steps |
| Observability | [infra](infra) (OTel -> Jaeger) | tracing multi-step reasoning chains |
| Token / cost optimization | [apps/api](apps/api) | prompt + semantic caching, cost metering |
| Cloud-native / MLOps | [infra](infra) | Docker, k8s, Terraform, drift monitoring (IaC + docs) |

For each "compare to X" choice, Groundwork builds one real implementation and documents the
alternatives in [docs/](docs). See [PLAN.md](PLAN.md) for the full blueprint,
[DECISIONS.md](DECISIONS.md) for why each choice was made, and [PROGRESS.md](PROGRESS.md)
for build status.

## Stack

Python / FastAPI - Next.js / TypeScript - LangGraph - Chroma (+ BM25 hybrid) - Rust (`ort`
ONNX rerank) - Claude / OpenAI / Ollama - OpenTelemetry / Jaeger - Docker Compose.

## Quick start

> Phase 0 scaffold. Services come online phase by phase (see [PROGRESS.md](PROGRESS.md)).

```bash
cp .env.example .env        # fill in ANTHROPIC_API_KEY / OPENAI_API_KEY
cd infra
docker compose config        # validate the skeleton parses
# docker compose up chroma jaeger ollama   # infra services (from Phase 1)
```

## Layout

```
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
```
