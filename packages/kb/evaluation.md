---
title: Evaluating foundation models
topic: evaluation
---

# Evaluating foundation models

Choosing a model for a task is an empirical question with three axes in tension: accuracy,
latency, and cost. A model that is more accurate is often slower and more expensive per token,
so the goal is not the best model but the best point on that frontier for the job.

## A golden set

Evaluation starts with a golden set: a fixed list of questions paired with known-good answers
or with the source passages a correct answer must use. The set should cover the real
distribution of queries, including the hard and adversarial ones, and it should be version
controlled so results are comparable over time. Without a golden set, "it seems better" is the
best claim anyone can make.

_Source: [Anthropic: Create strong empirical evaluations](https://docs.claude.com/en/docs/test-and-evaluate/develop-tests) - provider guidance on building eval sets that mirror the real task distribution._

## Scoring accuracy: retrieval versus answer

A RAG system has two places to measure, and conflating them hides where a failure comes from.

**Retrieval metrics** judge whether the right chunks were fetched at all, independent of the
generator: recall@k (did a relevant chunk make the top k), MRR (how early the first relevant
chunk appears), and nDCG (graded, rank-aware ordering). Low retrieval recall caps answer
quality no matter how good the model is, so this is the first thing to check.

**Answer metrics** judge the generated text. The field decomposes the doc's notion of
"groundedness" into named, separately measurable signals: faithfulness (every claim supported
by the retrieved context), answer relevancy (the answer addresses the question), context
precision (the retrieved context is relevant), and context recall (the needed context was
retrieved). Measuring them separately tells you whether to fix retrieval or generation.

_Source: [Ragas: Available metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) - canonical definitions of faithfulness, answer relevancy, and context precision/recall. Retrieval metrics: [Weaviate: Retrieval evaluation metrics](https://weaviate.io/blog/retrieval-evaluation-metrics)._

## LLM-as-a-judge and its biases

Accuracy can be scored by exact-match or overlap against expected sources, or by an
LLM-as-judge that reads the answer and context and rates support. Judges are convenient but
have known, named biases: position bias (favoring whichever answer comes first, mitigated by
swapping order), verbosity bias (favoring longer answers, mitigated by penalizing length), and
self-enhancement bias (rating its own model family higher, mitigated by masking model identity
or judging with a different model). Before trusting a judge, validate it by correlating its
scores against human labels.

_Source: [Evidently AI: LLM-as-a-judge guide](https://www.evidentlyai.com/llm-guide/llm-as-a-judge) - walks through building a judge, the named biases, and the human-label validation loop. Hands-on: [Hugging Face Cookbook: LLM-as-a-judge](https://huggingface.co/learn/cookbook/en/llm_judge)._

## Measuring latency and cost

Latency and cost are measured, not judged. Record wall-clock time per request and token counts
in and out, then price the tokens per the provider's rates. Reporting these alongside accuracy
turns a vague preference into a defensible tradeoff: model A is three points more accurate but
four times the cost and twice the latency, so model B wins for this use case.

## Comparing across providers

Running the same golden set through several providers (a frontier hosted model, a second
hosted model, and a local open-source model) puts them on one chart. The local model often
loses on accuracy but wins decisively on cost and data control, and for many internal tasks
that tradeoff is the right one. The comparison only means something when every model answers
the same questions under the same retrieval.

See also: rag, guardrails, cost.
