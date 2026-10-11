# Paste one prompt at a time into Codex

Before each prompt: open the `opspilot-starter` folder in Codex, read `AGENTS.md`,
run `python -m pytest -q`, and make a Git commit when the milestone is green.

## Day 1 — Understand and run the starter

> Read `README.md`, `AGENTS.md`, and the app source. Do not add features yet.
> Identify the execution flow for `/chat` and `/tickets`. Help me create a virtual environment,
> install requirements, and run pytest, FastAPI, and one OpenRouter request. Fix actual errors
> with the smallest changes. Explain each file with plain English and a request/response example.
> Do not hide failures or simulate model responses. Show exactly how to run the result.

**Pass:** `/health` responds; `/chat` gives real LLM response when key configured.

## Day 2 — RAG from real public documents

> Improve `scripts/ingest_docs.py` and `app/knowledge.py` without introducing a framework
> abstraction. Fetch only three official Kubernetes documentation pages. Store title, source
> URL, retrieval date, chunk ID and text. Replace lexical overlap with a simple ranked BM25
> retriever (or explain why lexical baseline suffices). Cite actual source URLs in every answer.
> Reject empty/garbled pages. Cache documents locally; make tests work without internet.
> Add tests for relevant and irrelevant questions. Explain chunking and retrieval tradeoffs.

**Pass:** a CrashLoopBackOff query retrieves the expected official page; offline tests pass.

## Day 3 — Clear LangGraph routing

> Refactor `app/workflow.py` into a readable LangGraph StateGraph with state fields question,
> intent, sources, diagnosis, answer and trace_steps. Add separate `knowledge` and `diagnose`
> paths using conditional edges. Use a deterministic keyword router for this MVP; don't create
> an unnecessary agent loop. Keep the LLM call in one module. Add tests proving correct routes
> and failure behavior. Return `trace_steps` in `/chat` so I can show routing during demo.
> Explain every node and edge in one small Mermaid diagram.

**Pass:** knowledge and diagnosis questions produce different trace paths.

## Day 4 — Real MCP integration

> Review official current MCP Python SDK v2 documentation at https://py.sdk.modelcontextprotocol.io/.
> Verify `app/mcp_server.py` and `app/mcp_client.py` against the INSTALLED SDK, not old FastMCP
> examples. Keep MCP over Streamable HTTP bound to 127.0.0.1:8001. Validate that the client can
> discover and call `search_runbooks` and `create_ticket`. Wire the LangGraph retrieval node
> to the MCP search tool (with explicit errors; no silent direct Python bypass). Keep SQLite
> approval enforcement inside the ticket business function. Add real MCP integration tests
> and show the tool list and request/response payloads. Use no bare HTTP REST call as an MCP substitute.

**Pass:** real MCP tool discovery/calls and blocked unapproved ticket; retry is idempotent.

## Day 5 — Real A2A inter-agent delegation

> Use official a2a-sdk docs/examples at https://github.com/a2aproject/a2a-samples/tree/main/samples/python/agents/helloworld.
> Pin the working a2a-sdk version. Create ONE independently running `diagnosis_agent` service
> on localhost:9000 using the real A2A Python SDK. Publish an Agent Card with a Kubernetes
> diagnosis skill. Send user-provided logs and symptoms through an A2A client from the
> LangGraph diagnosis node; return concise findings and uncertainty. Handle timeout, remote
> errors and malformed responses. Add one integration test verifying actual A2A transport.
> Do not replace A2A with a regular requests.post(). Explain agent card, client, task and artifact.

**Pass:** show Agent Card and an A2A request/response; failure is handled gracefully.

## Day 6 — Safety, evals, observability and packaging

> Add 12 realistic synthetic Kubernetes incidents across OOMKilled, ImagePullBackOff,
> CrashLoopBackOff, probe failures and bad configuration. Label them as synthetic.
> Add pytest evaluations for intent routing, retrieval relevance, unauthorized ticket creation,
> idempotency, missing API key and unreachable MCP/A2A. Add structured logs that omit secrets,
> measure elapsed time and model errors, and add a minimal Dockerfile/docker-compose for three
> local services. Do not invent measured pass rates; print calculated results from tests.

**Pass:** tests run without OpenRouter network access and failure scenarios are visible.

## Day 7 — Technical demo and interview preparation

> Prepare `DEMO.md` with a 7-minute walkthrough: system diagram, architecture choices,
> sample knowledge query, diagnostic A2A delegation, actual MCP tool call, approval rejection,
> successful ticket creation, duplicate retry, and tests. Update README with start/stop commands,
> design tradeoffs and limitations. Produce 10 interview questions and factual answers based only
> on the code in this repository. Remove dead code; do not add new features.

**Pass:** complete live demo is rehearsable with three local processes and reproducible commands.

## Codex repair prompt (use anytime something breaks)

> Read the failing stack trace and the relevant test. Explain the root cause in 3 sentences.
> Make the smallest possible fix, add a regression test, run the targeted test followed by all
> tests, and show the exact commands and results. Do not rewrite unrelated modules.
