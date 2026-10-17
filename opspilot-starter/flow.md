# Operational flows

## Chat: implemented

```mermaid
flowchart TD
    U[POST /chat: question] --> V[FastAPI validates Question]
    V --> C[workflow.classify: intent label]
    C --> R[knowledge.search_docs: read data/docs.json]
    R --> E{Relevant passages?}
    E -->|No| N[Return no relevant documentation message]
    E -->|Yes| K{Key and model set?}
    K -->|No| P[Labelled retrieval preview]
    K -->|Yes| L[llm.generate_answer: OpenRouter HTTPS POST]
    L --> A[Actual model answer or propagated error]
    N --> O[API returns intent, answer, sources]
    P --> O
    A --> O
```

Classification does not branch the graph. `/chat` never creates a ticket or invokes MCP. An upstream OpenRouter exception currently becomes HTTP 500, rather than a successful response with a fabricated answer.

## Tickets: implemented local demo

```mermaid
sequenceDiagram
    actor User
    participant API as FastAPI
    participant DB as Shared SQLite
    participant MCP as Local MCP server
    User->>API: POST /tickets/drafts (title, summary)
    API->>DB: Store unapproved draft
    API-->>User: 201, draft_id and approved=false
    User->>API: POST /tickets/drafts/{id}/approve (demo code)
    alt Missing or wrong demo code
        API-->>User: 503 or 403
    else Correct code
        API->>DB: Mark draft approved (404 if absent)
        API->>MCP: create_ticket via real MCP client
        MCP->>DB: Check approval, return existing ticket or insert
        MCP-->>API: MCP tool result
        API-->>User: 200, draft_id and string mcp_tool_result
    end
    User->>API: GET /tickets
    API->>DB: Read tickets
    API-->>User: 200, JSON array
```

If MCP is unavailable, approval returns 503 and the draft stays approved. Retry after restoring MCP. The code verifies sequential retry idempotency; it does not guarantee every concurrent request succeeds.

| Operation | Input | Output / failure | Storage effect |
| --- | --- | --- | --- |
| `GET /health` | None | 200 status and service | None |
| `POST /chat` | Question, 3–2000 characters | 200 intent/answer/sources; 422 invalid input; upstream errors may become 500 | None |
| `POST /tickets/drafts` | Title 3–150, summary 3–2000 characters | 201 draft ID and false approval; 422 invalid input | Inserts draft |
| `POST /tickets/drafts/{id}/approve` | Approval code string | 200 result; 403 wrong code; 404 missing draft; 503 missing code or MCP failure | Approves draft; MCP may insert ticket |
| `GET /tickets` | None | 200 array, possibly empty | Creates schema if needed, then reads |

## User registration: not implemented

There is no registration endpoint, users table, password handling, session, or identity-provider integration. The demo approval code does not register or identify a user. The following is a proposed process only; it requires a separate feature request and ADR before implementation.

```mermaid
flowchart LR
    A[Proposed: user starts registration] --> B[External identity provider]
    B --> C[Verify identity under chosen provider policy]
    C --> D[Application validates token and maps roles]
    D --> E[Authorize operations by user and resource]
```

| Proposed stage | Decision still needed | Current implementation |
| --- | --- | --- |
| Register / sign in | Identity provider and OIDC flow | Absent |
| Establish identity | Token validation, session lifetime | Absent |
| Authorize access | Ownership and role policy | Shared local demo approval code only |
| Audit actions | Retention and privacy policy | No production audit system |

## Development and deployment

The repository has no CI workflow, container definition, or deployment configuration. The local development routine below is executable; automated CI/CD remains a proposal.

| Stage | Current local command / action | Automation status |
| --- | --- | --- |
| Install | `python -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.txt` | Manual; dependencies have version ranges, no lockfile |
| Validate | `.venv/bin/python -m pip check` and `.venv/bin/python -m pytest -q` | Manual; 6 tests passed |
| Start | API and MCP commands in [entrypoint.md](entrypoint.md) | Manual, two processes |
| Smoke check | Health, retrieval preview, MCP discovery, approved ticket retry | Manual; verified locally |
| Publish code | Commit reviewed files and push a branch | Git operation, not application deployment |
| Deploy | Choose target, packaging, secrets, database persistence, authentication and rollback | Not configured |

```mermaid
flowchart LR
    A[Local checkout] --> B[Install requirements]
    B --> C[pip check and pytest]
    C --> D[Run API and MCP]
    D --> E[Functional smoke checks]
    E --> F[Commit and push code]
    F -. Proposed automation .-> G[CI install and tests]
    G -. Not configured .-> H[Build artifact]
    H -. Needs deployment design .-> I[Deploy and smoke check]
    I -. Needs rollback design .-> J[Promote or roll back]
```

An OpenRouter smoke request is manual and needs credentials/network permission. Never add credentials to source control or assume that offline tests validate model availability.
