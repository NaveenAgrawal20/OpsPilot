# OpsPilot repository instructions for Codex

You are helping a Python beginner prepare an honest technical interview demonstration in one week.

- Prefer readable functions and simple modules; avoid abstract base classes and elaborate frameworks.
- Keep business logic separate from FastAPI routes and protocol SDK adapters.
- Implement one milestone per prompt. Explain each changed file in plain English.
- For each feature, add a pytest test, run tests, and provide a curl command to verify it.
- Do not hard-code API keys or push .env.
- Do not fabricate model outputs, external calls, MCP invocations, or A2A messages.
- Use official SDK docs for the versions installed; preserve actual MCP/A2A protocol usage.
- Do not auto-create incident tickets in a troubleshooting node. Require approval first.
- Keep MCP bound to 127.0.0.1 and explicitly label demo-only authorization.
- If package APIs have changed, first make the smallest compatibility fix and cite the relevant official docs in the commit message.
- After each change summarize: WHAT changed, WHY, HOW to test, and interview explanation.
