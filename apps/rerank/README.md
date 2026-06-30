# apps/rerank

Rust microservice that reranks retrieval candidates with an ONNX cross-encoder (via the
`ort` crate), exposed over REST. It sits on the RAG hot path: hybrid search returns a
candidate set, this service scores query-document pairs and reorders them before the agent
reads context.

Why Rust: reranking is the genuine latency-sensitive step in the pipeline, so it is the one
place a compiled service earns its keep and shows the polyglot boundary cleanly.

**Built in:** Phase 7 (stubbed in Phase 2). Stub until then.
