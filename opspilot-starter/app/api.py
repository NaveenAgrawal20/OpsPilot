"""FastAPI boundary: validate requests and delegate to simple business functions."""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .tickets import approve_draft, list_tickets, prepare_draft

app = FastAPI(title="OpsPilot", version="0.1.0")


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


class TicketDraft(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    summary: str = Field(min_length=3, max_length=2000)


class Approval(BaseModel):
    approval_code: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "opspilot"}


@app.post("/chat")
def chat(request: Question) -> dict:
    # Lazy import leaves /health testable without an installed agent SDK.
    from .workflow import graph
    state = graph.invoke({"question": request.question})
    return {"intent": state["intent"], "answer": state["answer"],
            "sources": [{"title": p["title"], "url": p["url"]} for p in state["sources"]],
            "trace_steps": state["trace_steps"]}


@app.post("/tickets/drafts", status_code=201)
def draft_ticket(request: TicketDraft) -> dict:
    return prepare_draft(request.title, request.summary)


@app.post("/tickets/drafts/{draft_id}/approve")
async def approve_and_create(draft_id: str, request: Approval) -> dict:
    expected_code = os.getenv("DEMO_APPROVAL_CODE")
    if not expected_code:
        raise HTTPException(status_code=503, detail="Set DEMO_APPROVAL_CODE")
    if request.approval_code != expected_code:
        raise HTTPException(status_code=403, detail="Invalid demo approval code")
    try:
        approve_draft(draft_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        from .mcp_client import execute_ticket_tool
        outcome = await execute_ticket_tool(draft_id)
    except Exception as exc:
        # Draft stays approved; calling again is safe because tool is idempotent.
        raise HTTPException(status_code=503, detail="MCP ticket service unavailable") from exc
    return {"draft_id": draft_id, "mcp_tool_result": outcome}


@app.get("/tickets")
def tickets() -> list[dict]:
    return list_tickets()
