# OpsPilot — 7-day Codex build kit

This is an **educational, enterprise-style project**, not a production service.
The starter provides a small FastAPI app, a 3-step LangGraph workflow,
lexical RAG with source URLs, local SQLite incident drafts/tickets,
and an MCP v2 server/client integration. It does **not** yet provide A2A;
Day 5 in `PROMPTS.md` implements the real A2A protocol using the official SDK.

## What is real and what is simulated?

- Real: Python code, LangGraph graph, OpenRouter request, web document ingestion,
  official MCP protocol tool server/client, SQLite persistence, tests.
- Simulated: enterprise service-desk tickets, approval authentication via a local demo code,
  incident logs. Do not describe these as production identity or ServiceNow integration.
- Day 2 upgrades the starter corpus: bundled entries are short paraphrased summaries with source
  links, *not* the full text of the live websites. Run the ingestion script to fetch current text.
- Day 5 adds one independently running A2A diagnosis agent.

## Prerequisites

See [entrypoint.md](entrypoint.md) for exact run commands, each file's purpose,
request/response examples, and the latest verification record.
[decisions.md](decisions.md) records architecture choices and an ADR template;
[flow.md](flow.md) diagrams the existing flows and labels registration/CI/CD proposals.

Python 3.11+; Internet to install packages, download docs and use OpenRouter;
Codex CLI or Codex IDE extension. An OpenRouter key and a valid current model ID
are needed for generated answers. Retrieval preview and ticket demo work without an LLM key.

## Start on your laptop

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
# Edit .env: put OPENROUTER_API_KEY, OPENROUTER_MODEL, DEMO_APPROVAL_CODE.
python -m pytest -q
```

**Run the API (terminal 1):**

```bash
python -m uvicorn app.api:app --reload --host 127.0.0.1 --port 8000
```

**Run the real MCP tool server (terminal 2):**

```bash
python -m app.mcp_server
```

**On Day 2, download official Kubernetes docs** (replaces seed summary corpus):

```bash
python scripts/ingest_docs.py
```

## Demo commands

### 1. Health

```bash
curl http://127.0.0.1:8000/health
```

### 2. Ask the graph (key optional; without key the answer is labelled a retrieval preview)

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Why is my Kubernetes pod OOMKilled and restarting?"}'
```

### 3. Prepare ticket (no ticket created yet)

```bash
curl -X POST http://127.0.0.1:8000/tickets/drafts \
  -H 'Content-Type: application/json' \
  -d '{"title":"Kubernetes OOMKilled","summary":"Pod restarts; investigate memory limit."}'
```

Copy the resulting `draft_id` and substitute it below. Keep the MCP server running.

### 4. Approve it (calls the ticket tool over MCP)

```bash
curl -X POST 'http://127.0.0.1:8000/tickets/drafts/PASTE_DRAFT_ID/approve' \
  -H 'Content-Type: application/json' \
  -d '{"approval_code":"YOUR_DEMO_APPROVAL_CODE"}'
curl http://127.0.0.1:8000/tickets
```

Without a valid approval code, FastAPI returns HTTP 403. Without a running MCP
server, ticket creation returns HTTP 503 and the approved draft can be retried.
Calling the same approval twice should not create duplicate tickets.

## Files worth understanding

| File | One job |
| --- | --- |
| `app/api.py` | Receive requests and return responses |
| `app/workflow.py` | Define LangGraph nodes and execution order |
| `app/knowledge.py` | Retrieve passages and source URLs |
| `app/llm.py` | Make one OpenRouter chat-completion request |
| `app/tickets.py` | Persist drafts and approved tickets in SQLite |
| `app/mcp_server.py` | Expose two tools using actual MCP protocol |
| `app/mcp_client.py` | Invoke the MCP server over Streamable HTTP |
| `scripts/ingest_docs.py` | Download public docs for RAG |
| `tests/` | Explainable safety and smoke tests |
| `PROMPTS.md` | One Codex prompt per day |

## Known MVP limitations (say this in the interview)

- Current retrieval is lexical token overlap, not embeddings/hybrid/vector search.
- Ticket approval uses a demo code, not Entra ID or real authorization.
- The LangGraph graph currently classifies but does not route differently by intent.
  Extend with conditional edges during Day 3.
- The starter is not yet fully wired to A2A; use the official A2A Python SDK on Day 5.
- No production-grade auth, telemetry, centralized logging or deployed scaling yet.
- Published docs must be reviewed for usage rights, accuracy and change over time.
- Local validation on 2026-10-11 passed all 6 tests with MCP 2.3.0, plus live API
  retrieval and MCP ticket approval/retry checks. OpenRouter completion remains
  unverified: key/model were absent and the environment proxy rejected connectivity.
