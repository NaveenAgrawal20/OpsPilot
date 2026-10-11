# Run and understand OpsPilot

Run commands from `opspilot-starter`, not the repository root. In this cloud checkout:

```bash
cd /workspace/OpsPilot/opspilot-starter
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -m pytest -q
```

Python 3.11+ is required. Verified on Python 3.12.14 with MCP 2.3.0; all 6 tests passed. Requirements use version ranges, so a fresh install can resolve different versions. On Windows activate with `.venv\Scripts\Activate.ps1` instead.

## Configuration

Create `.env` only if it does not already exist:

```bash
test -e .env || cp .env.example .env
```

Edit it locally, or supply credentials securely in cloud environment settings. Never commit `.env` or put a key in chat. Replace the example `DEMO_APPROVAL_CODE` with your own local demo code. `app/__init__.py` loads `.env` when the package is imported, and exported environment variables take precedence. Restart both processes after changing configuration.

| Variable | Purpose | Needed for |
| --- | --- | --- |
| `OPENROUTER_API_KEY` | Real OpenRouter credential | Generated answers |
| `OPENROUTER_MODEL` | Current model ID available to your account | Generated answers |
| `DEMO_APPROVAL_CODE` | Shared demo-only approval code | Ticket approval |
| `OPSPILOT_DB` | SQLite path, default `data/opspilot.db` | Both processes must point to the same file |
| `MCP_URL` | Default `http://127.0.0.1:8001/mcp` | API-to-MCP ticket invocation |

## Start the services

Terminal 1, from `opspilot-starter`:

```bash
source .venv/bin/activate
python -m uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Terminal 2, same directory:

```bash
source .venv/bin/activate
python -m app.mcp_server
```

MCP is deliberately bound to `127.0.0.1:8001` for the demo. Use Ctrl+C to stop each process. If a port is occupied, inspect the owning process rather than launching a duplicate or killing unrelated services.

## Requests and responses

Terminal 3:

```bash
curl --fail-with-body http://127.0.0.1:8000/health
curl --fail-with-body http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Why is my Kubernetes pod OOMKilled and restarting?"}'
```

Health returns `{"status":"ok","service":"opspilot"}`. With no key/model, the actual observed chat response was:

```json
{
  "intent": "diagnose",
  "answer": "Retrieved evidence (LLM not configured): Kubernetes: Debug Running Pods, Kubernetes: Assign Memory Resources, Kubernetes: Images",
  "sources": [
    {"title": "Kubernetes: Debug Running Pods", "url": "https://kubernetes.io/docs/tasks/debug/debug-application/debug-running-pod/"},
    {"title": "Kubernetes: Assign Memory Resources", "url": "https://kubernetes.io/docs/tasks/configure-pod-container/assign-memory-resource/"},
    {"title": "Kubernetes: Images", "url": "https://kubernetes.io/docs/concepts/containers/images/"}
  ]
}
```

This is retrieval, not a model response. The generic word overlap even matches the Images summary; this illustrates the lexical retriever's limitations.

Create a draft; this stores no ticket yet:

```bash
curl --fail-with-body http://127.0.0.1:8000/tickets/drafts \
  -H 'Content-Type: application/json' \
  -d '{"title":"Kubernetes OOMKilled","summary":"Pod restarts; investigate memory limit."}'
```

Response shape: `{"draft_id":"<generated UUID>","approved":false}` (HTTP 201). IDs below are placeholders, not fabricated observed results.

For explicit local demo approval, replace `PASTE_DRAFT_ID` with the returned draft ID. This Python command loads the local code without putting it into shell history; it makes the same JSON request as curl:

```bash
python - PASTE_DRAFT_ID <<'PY'
from dotenv import load_dotenv
import os
import sys
import requests
load_dotenv('.env')
draft_id = sys.argv[1]
code = os.getenv('DEMO_APPROVAL_CODE')
if not code:
    raise SystemExit('Set DEMO_APPROVAL_CODE first')
response = requests.post(
    f'http://127.0.0.1:8000/tickets/drafts/{draft_id}/approve',
    json={'approval_code': code}, timeout=30,
)
print(response.status_code, response.text)
response.raise_for_status()
PY
curl --fail-with-body http://127.0.0.1:8000/tickets
```

Approval returns `{"draft_id":"<UUID>","mcp_tool_result":"<actual MCP result as a string>"}`. Listing returns an array of ticket objects with `id`, `draft_id`, `title`, `summary`, and `status`; `[]` means no tickets. A ticket ID has the form `INC-<8 uppercase hex characters>`. Sequential repeat approval returns the same ticket. Wrong code returns `{"detail":"Invalid demo approval code"}` with 403. Missing draft returns 404; missing approval configuration or unavailable MCP returns 503. Invalid body lengths return FastAPI's validation detail with 422.

## One real OpenRouter completion

After configuring the key, a current model ID, and HTTPS access to `openrouter.ai`, this calls the existing model function exactly once with real retrieved passages. It fails visibly if configuration or the provider request fails; it never substitutes a sample model answer:

```bash
python - <<'PY'
from app.knowledge import search_docs
from app.llm import generate_answer
question = 'Why is my Kubernetes pod OOMKilled and restarting?'
print(generate_answer(question, search_docs(question)))
PY
```

Request: HTTPS POST `https://openrouter.ai/api/v1/chat/completions`, bearer authentication, your configured `model`, `temperature: 0.1`, and system/user messages containing the question and cited excerpts. Response: the actual `choices[0].message.content` string. No generated response example is included because no completion was obtained in this cloud instance.

The attempted real GET to `https://openrouter.ai/api/v1/models` failed at the proxy with `Tunnel connection failed: 403 Forbidden`. Both key and model were absent. Executing the completion command above failed before making its HTTP request with `RuntimeError: Set OPENROUTER_API_KEY and OPENROUTER_MODEL in .env`. The environment draft now declares them and adds `openrouter.ai`; saving the draft does not enable current runtime access or supply a key. Review/save the settings, enter the key securely, and publish as required by the environment UI. Retry after runtime configuration changes. No authenticated completion request was sent. `/chat` also invokes this function when both variables are set; upstream exceptions currently become HTTP 500.

## Every source file in plain English

| File | One job | Concrete input → output example |
| --- | --- | --- |
| `app/__init__.py` | Loads local settings when `app` is imported | Import `app` → `.env` fills unset environment variables; no HTTP response |
| `app/api.py` | Validates HTTP requests and delegates work | `GET /health` → status JSON; `POST /chat` → intent/answer/sources |
| `app/workflow.py` | Runs classify, retrieve, then explain | OOMKilled question → `diagnose`, passages, preview or actual model answer |
| `app/knowledge.py` | Counts shared lowercase words in bundled passages | `search_docs('OOMKilled memory limit')` → ranked passage dictionaries with URLs and scores |
| `app/llm.py` | Sends the question and evidence to OpenRouter | Question + passages → one real completion string, or visible exception |
| `app/tickets.py` | Stores drafts, approval, and local tickets | Title + summary → unapproved draft; approved draft ID → persistent ticket |
| `app/mcp_server.py` | Exposes search and approved ticket creation as MCP tools | `search_runbooks` with query → passages; `create_ticket` with approved ID → ticket |
| `app/mcp_client.py` | Calls the separate MCP server | Approved draft ID → actual tool result converted to a string; error result → exception |
| `scripts/ingest_docs.py` | Downloads and splits official Kubernetes pages | Three real HTTPS pages → replaces `data/docs.json`; request/parsing failure → exception |

| Supporting file | Purpose and example |
| --- | --- |
| `data/docs.json` | Bundled paraphrased summaries with real URLs; retrieval reads them, not live web pages |
| `requirements.txt` | Installs Python dependencies; there is no lockfile |
| `.env.example` / `.gitignore` | Configuration names and ignored local secrets, virtualenv, caches, databases |
| `tests/test_api.py` | Health and invalid approval; temporary DB prevents persistent test tickets |
| `tests/test_knowledge.py` | Tokenization and retrieval source URLs |
| `tests/test_tickets.py` | Approval required and sequential retry idempotency |
| `tests/test_mcp.py` | Actual in-process MCP discovery/search; skipped if MCP is absent, passed here |
| `README.md` / `AGENTS.md` | Project overview and contributor rules |
| `PROMPTS.md` / `DEMO_SCRIPT.md` | Future milestone prompts and interview demonstration guidance |
| `decisions.md` | Retrospective ADRs and a template for future choices |
| `flow.md` | Implemented request diagrams and clearly labelled proposed registration/deployment processes |
| `entrypoint.md` | This executable guide and source explanation |

Interview explanation: FastAPI is the front door, LangGraph orders chat steps, local summaries provide evidence, OpenRouter optionally writes the answer, and a separate MCP service creates only explicitly approved demo tickets in shared SQLite.

## Verification record (2026-10-11)

- Virtual environment creation, requirements installation and `pip check`: passed.
- `pytest -q`: 6 passed, none skipped.
- Plain README API and MCP startup commands: passed.
- Live health and retrieval preview: passed; short question returned 422.
- Draft 201, wrong approval 403, real MCP approval 200, sequential retry 200, listing 200: passed. A labelled local smoke-test ticket was retained in ignored SQLite storage.
- OpenRouter connectivity: failed at environment proxy with 403. Completion command: failed with missing-key/model RuntimeError before sending an authenticated request; no model response obtained.
- No application code change was required by the observed local checks. This milestone adds documentation and corrects the stale README verification claim; no new features were added.
