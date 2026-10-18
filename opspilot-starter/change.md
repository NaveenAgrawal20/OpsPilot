# Day 3 changes

## What changed

The chat workflow now has two clear paths:

```text
Question → router → knowledge or diagnose → answer
```

- `router` looks for operational words such as `OOMKilled`, `restart`, and `error`.
- `knowledge` handles general questions, such as “What is a container image?”
- `diagnose` handles problem questions, such as “Why is my pod restarting?”
- Both paths retrieve Kubernetes documentation and then go to one `answer` step.
- `/chat` now returns `trace_steps`, so the demo can show which path ran.
- The workflow state now keeps the question, selected intent, sources, diagnosis note, answer, and trace steps.
- New tests check both routes, no-documentation handling, visible retrieval failures, and the `/chat` trace.

## Why it changed

Previously, every question followed the same path. The app labelled a question as
`knowledge` or `diagnose`, but that label did not change what happened next.

The new workflow makes the label useful. A general question and a troubleshooting
question now follow different named paths. This makes the project easier to
explain during a demo and leaves a clear place to add more diagnosis work later.

`trace_steps` makes the routing visible. For example, a pod restart question
returns:

```json
[
  "router:diagnose",
  "diagnose:retrieved_evidence",
  "answer:completed"
]
```

## Decisions

### Use a deterministic keyword router

The router uses a short fixed list of troubleshooting keywords instead of asking
the LLM to decide the route.

Why: it is predictable, fast, free to run, and easy to explain. A keyword router
is limited: it can miss a problem described with different words. That is an
acceptable trade-off for this MVP.

### Keep one answer node

Both paths meet at one `answer` node.

Why: OpenRouter calls remain in `app/llm.py`, and answer generation is not copied
into multiple workflow nodes. This keeps the code small and avoids inconsistent
answer behavior.

### Do not add an agent loop

Each request chooses one route and finishes after one answer.

Why: a loop would add complexity without helping the current demo. The workflow
does not repeatedly call tools or make hidden decisions.

### Show failures instead of hiding them

No matching documents return a clear no-documentation message. A broken corpus
lookup raises its error instead of pretending the request worked.

Why: the demo should be honest about missing evidence and broken dependencies.
