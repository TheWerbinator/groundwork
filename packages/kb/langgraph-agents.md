---
title: LangGraph agents
topic: langgraph-agents
---

# LangGraph agents

LangGraph models an agent as a state graph: nodes are steps, edges are transitions, and a
shared state object is threaded through every node. This is a more explicit and debuggable way
to build an agent than a single while-loop around a model, because the control flow is data
you can inspect, draw, and test.

## State, nodes, and edges

The **state** is a typed dictionary (a `TypedDict`) that accumulates the run: the question,
retrieved context, the draft answer, critic feedback, a retry count. A **node** is a function
that takes the state and returns an update to it. An **edge** connects nodes; a **conditional
edge** chooses the next node by inspecting the state, which is how loops and branches are
expressed. The graph type itself is `StateGraph`, parameterized by the state schema.

_Source: [LangGraph: Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) - authoritative reference for StateGraph, state schemas, nodes, and conditional edges._

## Reducers: how state accumulates

"Accumulates" hides an important mechanism. Each state key has a reducer that decides how a
node's update is merged in. With no reducer, a key is overwritten by each update. To grow a
value instead, such as appending to a message history or incrementing across a loop, the key
declares an accumulating reducer (for example `Annotated[list, operator.add]`). Getting this
right is what makes the difference between a state that remembers and one that silently
clobbers itself, and it is the most common beginner stumbling point.

_Source: [LangGraph: Graph API (state and reducers)](https://docs.langchain.com/oss/python/langgraph/graph-api) - defines reducers and the `Annotated` accumulation pattern._

## A grounded-answer graph

A typical RAG agent graph: a planner node decides what to retrieve, a retriever node runs
hybrid search, a drafter node writes an answer from the retrieved context, and a critic node
checks whether the answer is grounded and complete. A conditional edge from the critic either
finishes or loops back to retrieve more, up to a retry limit. The retry limit lives in the
state, so the loop cannot run forever.

## Self-reflection

The critic node is what makes the agent self-reflective: the model evaluates its own draft
against the context and decides whether to accept it or try again with different retrieval or
a revised plan. Keeping the critic as a separate node, rather than folding it into the
drafter, keeps the two concerns testable in isolation. This drafter-then-critic shape is the
evaluator-optimizer pattern from Anthropic's agent-patterns taxonomy.

_Source: [Anthropic: Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents) - vendor-neutral taxonomy including the evaluator-optimizer loop this mirrors._

## Persistence and resuming

A graph can save its state at each step through a checkpointer. With checkpointing on, a run
can be paused for human review and resumed later, recover from a crash, or branch to explore
alternatives, all because the state at every super-step is persisted. This is the feature
behind the claim that the flow can be audited and resumed.

_Source: [LangGraph: Graph API (persistence)](https://docs.langchain.com/oss/python/langgraph/graph-api) - covers checkpointers and resuming from saved state._

## Why a graph over alternatives

AutoGen models agents as conversational participants exchanging messages, and CrewAI models
them as roles on a crew with assigned tasks (Agents, Tasks, Tools, Crew). Both are productive,
but they hide control flow inside a conversation or a role hierarchy. LangGraph's explicit
graph makes the control flow a first-class, inspectable artifact, which is the right tradeoff
when the flow needs to be audited, traced, and resumed. One currency note for anyone choosing
today: the original AutoGen is in maintenance mode, with Microsoft steering new work toward its
successor framework, so weigh the comparison on the model rather than on momentum.

_Source: [LangChain Academy: Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph) - free official course building state, memory, human-in-the-loop, and self-correcting agents. CrewAI side: [CrewAI Concepts](https://docs.crewai.com/en/concepts/tasks)._

See also: mcp, guardrails, evaluation.
