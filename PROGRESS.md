# Progress

Running log of what is built, phase by phase. Newest entries at the top of each phase.

## Phase 0 - Bootstrap (in progress)

- Repo scaffolded: `apps/`, `packages/`, `eval/`, `infra/`, `docs/` directories.
- `.gitignore` with `.env*` guarded (`!.env.example`), polyglot rules (Python + Node + Rust).
- `.env.example` with placeholder keys.
- `infra/docker-compose.yml` skeleton (services declared, not yet wired).
- `README.md` index mapping each capability to its component.
- Planning docs: `PLAN.md`, `PROGRESS.md`, `DECISIONS.md`.

## Phase status

| # | Phase | Status |
|---|---|---|
| 0 | Bootstrap | in progress |
| 1 | Corpus + ingestion | not started |
| 2 | Hybrid retrieval | not started |
| 3 | Agent v1 (LangGraph) | not started |
| 4 | Guardrails | not started |
| 5 | Self-reflection + critic | not started |
| 6 | MCP | not started |
| 7 | Rust rerank service | not started |
| 8 | HITL UI | not started |
| 9 | Observability | not started |
| 10 | Eval harness | not started |
| 11 | Infra + docs | not started |
