# Architecture decisions

These records describe choices observed in the starter source on 2026-10-11.
They are retrospective documentation, not a claim about earlier design meetings.
No new feature or authentication protocol is implemented by these records.

## ADR-001: SQLite for local incident storage

- **Status:** Implemented in the starter
- **Context:** The educational demo needs drafts and tickets to survive process restarts without running a database service.
- **Decision:** Use Python's SQLite driver in `app/tickets.py`. FastAPI and MCP must use the same `OPSPILOT_DB` path. A unique `tickets.draft_id` prevents duplicate stored tickets.
- **Alternatives:** In-memory storage loses data on restart; PostgreSQL adds a service and operational work.
- **Consequences:** Simple local setup and persistent data. This is not a production service desk. Concurrent approvals can still race between the lookup and insert and raise a uniqueness error; sequential retries are verified.
- **Verification:** `tests/test_tickets.py` checks approval and sequential idempotency using a temporary database.

## ADR-002: Explicit approval using a demo code

- **Status:** Implemented for local demo only
- **Context:** Diagnosis must not automatically create tickets.
- **Decision:** Require `DEMO_APPROVAL_CODE` at the approval endpoint, then mark the draft approved before invoking the MCP tool. The tool independently checks stored approval.
- **Alternatives:** Real OIDC/OAuth-based user identity would require an identity provider, token validation, roles, and ownership rules. None exists here.
- **Consequences:** Wrong code returns 403; missing configuration returns 503. The shared code is not user registration, login, or production authorization. Chat, draft creation, ticket listing, and the local MCP server have no user authentication. MCP stays on `127.0.0.1`.
- **Verification:** API tests reject wrong approval; ticket tests reject unapproved drafts. Live HTTP approval and repeated approval were checked.

## ADR-003: A small graph and lexical retrieval

- **Status:** Implemented in the starter
- **Context:** The workflow should be easy to explain and cite its evidence.
- **Decision:** LangGraph executes classify → retrieve → explain. Retrieval ranks bundled summaries by shared words and returns up to three passages. Intent labels do not change routing. Without a key/model, explanation is explicitly a retrieval preview.
- **Alternatives:** Vector search and conditional graph routing add dependencies and behavior outside this milestone.
- **Consequences:** Easy to inspect, but common words can return weak matches. Bundled text is a summary, not downloaded full documentation. No model answer is fabricated.
- **Verification:** Retrieval tests, plus a live `/chat` request with nonempty sources and the preview label.

## ADR-004: OpenRouter HTTP and a separate real MCP service

- **Status:** Implemented; authenticated OpenRouter execution remains unverified
- **Context:** Keep route handling, model calls, storage, and protocol adapters separate.
- **Decision:** `app/llm.py` sends an HTTPS chat-completions request through `requests`. `app/mcp_client.py` uses the official MCP client to invoke the separate server over Streamable HTTP. `/chat` uses local retrieval; it does not call MCP.
- **Alternatives:** A single process is simpler to operate, but would not demonstrate the service boundary. A2A is a future milestone and is not present.
- **Consequences:** Two local processes and one shared database path are required for ticket approval. OpenRouter needs a real key, model ID, and network permission. HTTP/model failures currently propagate as an API 500; MCP approval failures return 503 while keeping the draft approved for retry. The MCP result is currently returned as a string, not a typed ticket response.
- **Verification:** All six existing tests pass with MCP 2.3.0. Live ticket creation uses actual MCP. OpenRouter models discovery was attempted but the environment proxy returned 403 before contacting the service; no generated completion was obtained.

## Template for the next ADR

```markdown
## ADR-NNN: Short decision title

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Implemented | Superseded by ADR-NNN
- **Context:** What concrete problem and constraints require a choice?
- **Decision:** What will we use, and where does it apply?
- **Alternatives:** What other choices were considered, and why not use them?
- **Consequences:** Benefits, costs, technical trade-offs, and remaining risks.
- **Verification:** Tests or operational evidence; distinguish planned from executed checks.
```

Keep this lowercase `decisions.md` as the canonical ADR file to avoid two diverging copies on case-sensitive systems.
