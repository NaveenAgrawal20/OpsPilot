# Interview demo script (update after Day 7)

0:00 — Business scenario: a K8s pod is restarting; the support desk needs grounded diagnosis.
0:30 — Show Python/FastAPI boundary and LangGraph state and nodes.
1:30 — Run `/chat`; show sources and distinguish evidence from LLM explanation.
2:30 — Show real MCP Inspector/SDK tool discovery; search an official runbook.
3:30 — Show remote A2A Agent Card and diagnosis request (requires Day 5 implementation).
4:30 — Prepare ticket. Attempt unauthorized creation; show rejection.
5:00 — Approve and create ticket via MCP; demonstrate idempotent retry.
6:00 — Run tests and show errors/latency logs.
6:30 — Explain limitations: demo authentication, synthetic incidents, RAG baseline and no cloud hosting.

Interview framing:
"I designed a locally deployable enterprise-style IT incident assistant using public Kubernetes
runbooks and synthetic diagnostic evidence. The service demonstrates orchestration, retrieval,
protocol-based tool integration, inter-agent delegation, controlled state changes, and testability.
It is a portfolio simulation, not a client production deployment."
