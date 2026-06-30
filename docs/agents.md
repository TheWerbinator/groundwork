# The LangGraph agent: planner, retriever, drafter

> A guided walkthrough of the agent in [`apps/api`](../apps/api). New to LangGraph? This is the
> page to read slowly. For the concept, see
> [packages/kb/langgraph-agents.md](../packages/kb/langgraph-agents.md); this page shows how our
> code implements it, and ends with a real trace you can reproduce.

## What you'll learn

- What a LangGraph "state graph" actually is: state, nodes, edges.
- How our agent turns a question into a grounded, cited answer in three steps.
- What a *reducer* is and why state needs one.
- How to *watch* the graph run, node by node, with `--trace`.

## The big idea

A LangGraph agent is a graph you can draw. **Nodes** are steps (functions). **Edges** say which
step runs next. A single **state** object is threaded through every node: each node reads it and
returns updates. That is the whole model. The payoff over a hidden `while` loop is that the
control flow is data you can inspect, stream, and test one node at a time.

Our v1 graph is a straight line:

```
START -> planner -> retriever -> drafter -> END
```

[`agent/graph.py`](../apps/api/src/groundwork_api/agent/graph.py)'s `build_agent` is literally
those four edges. Phase 5 will bend the line into a loop by adding a critic node and a
*conditional* edge back to the retriever.

## The state

[`agent/state.py`](../apps/api/src/groundwork_api/agent/state.py) defines `AgentState`, a
`TypedDict`. Each key is filled by one node:

| key | written by | meaning |
|---|---|---|
| `question` | input | the user's question |
| `search_query` | planner | focused query for retrieval |
| `chunks` | retriever | the grounding context |
| `answer` | drafter | the grounded answer |
| `citations` | drafter | sources the answer rests on |
| `notes` | every node | a running log (see reducers) |

### Reducers: how a key merges

When a node returns `{"search_query": "..."}`, LangGraph has to decide how to merge that into the
state. By default it **overwrites** the old value. That is right for `search_query` (one node
writes it once). But `notes` should **accumulate**, one entry per node. You get that by annotating
the key with a reducer:

```python
notes: Annotated[list[str], add]   # `add` = list concatenation, so updates append
```

Now `{"notes": ["planner did X"]}` is *appended* instead of replacing. That is the exact
mechanism the Phase 5 critic loop will use to accumulate retries. `notes` is also what `--trace`
prints, so you can see it grow.

## The nodes

[`agent/nodes.py`](../apps/api/src/groundwork_api/agent/nodes.py). Each node is built by a small
factory that closes over its dependencies, which keeps the node pure and testable.

- **planner** calls the LLM to rewrite the question into a focused search query. This is the
  smallest honest example of an agent "planning": it decides *how* to search. (A later phase lets
  it choose tools or decompose the question.)
- **retriever** calls the hybrid retriever from
  [packages/retrieval](../packages/retrieval) with that query and flattens the hits into `chunks`.
  It depends only on `.retrieve(query, top_k)`, so a fake stands in for it in tests.
- **drafter** assembles the chunks + question into a prompt (the RAG "augment" step), calls the
  LLM for a grounded answer, and derives `citations` from the chunks it grounded on.

The LLM is built by [`llm.py`](../apps/api/src/groundwork_api/llm.py), which returns a Claude,
GPT, or Ollama chat model based on `DEFAULT_PROVIDER`. The nodes only ever call
`.invoke(messages).content`, so they never know which provider answered. That uniform seam is
what the Phase 10 eval harness uses to compare models on the same questions.

## Run it

```bash
cd apps/api
uv sync
# needs the KB ingested (packages/ingestion: uv run ingestion ingest) and a provider in .env
uv run groundwork-api ask "how does reciprocal rank fusion work?"
```

Without a provider key you can still run the tests (they use a fake LLM) and the REST surface.
With a provider configured (`DEFAULT_PROVIDER=claude` + `ANTHROPIC_API_KEY`, or `ollama` for a
free local model), `ask` returns a grounded answer with a `Sources:` list.

## Watch it run: `--trace`

This is the point of building on a graph. `--trace` streams one event per node and prints what
each produced. Below is a real run with hybrid retrieval over the live index (the answer text is
stubbed here so the example needs no API key; with a provider it is the model's grounded answer):

```
=== graph trace (one block per node) ===

[planner]
   search_query: reciprocal rank fusion k constant origin
   note: planner: search query = 'reciprocal rank fusion k constant origin'

[retriever]
   chunks: 5 retrieved
     - hybrid-search > Reciprocal Rank Fusion  (score=0.0328)
     - hybrid-search > Reciprocal Rank Fusion  (score=0.0323)
     - hybrid-search > Reranking after fusion  (score=0.0315)
   note: retriever: 5 chunks for 'reciprocal rank fusion k constant origin'

[drafter]
   answer: RRF sums 1/(k+rank), k=60 [hybrid-search].
   note: drafter: answered from 3 sources
```

Read it top to bottom: the planner sets `search_query`, the retriever fills `chunks` from real
hybrid search, the drafter writes `answer` and `citations`, and `notes` grows by one line per
node, your reducer at work.

## The REST surface

[`app.py`](../apps/api/src/groundwork_api/app.py) wraps the graph in `POST /ask`. FastAPI builds
the OpenAPI schema from the pydantic models, so the Phase 8 Next.js frontend gets a typed client
for free. Run `uv run groundwork-api serve` and open `http://localhost:8000/docs`.

## Try this

1. **Trace a vague vs precise question.** Run `--trace` on "how do I make search better?" then on
   "what is the RRF k constant?". Watch how the planner's `search_query` differs and how that
   changes which chunks come back.
2. **Swap the provider.** Set `DEFAULT_PROVIDER=ollama` (free, local) and compare the answer to
   Claude's on the same question. Same graph, different model: that is the seam.
3. **Add a node (preview of Phase 5).** Sketch a `critic` node that reads `answer` + `chunks` and
   returns a note on whether every claim is grounded. You will turn it into a real loop with a
   conditional edge next phase.

## Design choices

The reasoning (linear v1 graph, factory-built nodes, provider-agnostic LLM seam, deterministic
citations, the `notes` reducer as a teaching device) is under "Phase 3 decisions" in
[DECISIONS.md](../DECISIONS.md).

## Where it goes next

- [Phase 4] **Guardrails** wrap this agent: input checks (PII, injection) and output checks
  (grounding enforcement) around the graph.
- [Phase 5] **Self-reflection**: a critic node + a conditional edge make the straight line a loop.
