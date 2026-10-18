"""A small, one-pass LangGraph workflow for knowledge and diagnosis questions."""

import os
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from .knowledge import format_citations, search_docs
from .llm import generate_answer


DIAGNOSIS_KEYWORDS = ("crash", "error", "failing", "oomkilled", "restart", "imagepull")


class AgentState(TypedDict, total=False):
    question: str
    intent: Literal["knowledge", "diagnose"]
    sources: list[dict]
    diagnosis: str
    answer: str
    trace_steps: list[str]


def add_trace(state: AgentState, step: str) -> list[str]:
    return [*state.get("trace_steps", []), step]


def route_question(state: AgentState) -> dict:
    """Choose one deterministic path; this MVP has no agent loop."""
    question = state["question"].lower()
    intent = "diagnose" if any(word in question for word in DIAGNOSIS_KEYWORDS) else "knowledge"
    return {"intent": intent, "trace_steps": add_trace(state, f"router:{intent}")}


def choose_path(state: AgentState) -> Literal["knowledge", "diagnose"]:
    return state["intent"]


def knowledge(state: AgentState) -> dict:
    """Retrieve documentation for a general how-to or reference question."""
    return {
        "sources": search_docs(state["question"]),
        "trace_steps": add_trace(state, "knowledge:retrieved_sources"),
    }


def diagnose(state: AgentState) -> dict:
    """Retrieve diagnostic evidence and record whether a diagnosis can be grounded."""
    sources = search_docs(state["question"])
    diagnosis = (
        "Diagnostic evidence retrieved; answer only from the cited sources."
        if sources else "No diagnostic evidence was found for this question."
    )
    return {
        "sources": sources,
        "diagnosis": diagnosis,
        "trace_steps": add_trace(state, "diagnose:retrieved_evidence"),
    }


def answer(state: AgentState) -> dict:
    """Produce an answer once, after either route has supplied sources."""
    sources = state["sources"]
    if not sources:
        result = "No relevant documentation found. Please provide more details."
        return {"answer": result, "trace_steps": add_trace(state, "answer:no_sources")}

    if not os.getenv("OPENROUTER_API_KEY") or not os.getenv("OPENROUTER_MODEL"):
        titles = ", ".join(source["title"] for source in sources)
        result = f"Retrieved evidence (LLM not configured): {titles}"
    else:
        result = generate_answer(state["question"], sources)
    return {
        "answer": result + format_citations(sources),
        "trace_steps": add_trace(state, "answer:completed"),
    }


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("router", route_question)
    workflow.add_node("knowledge", knowledge)
    workflow.add_node("diagnose", diagnose)
    workflow.add_node("answer", answer)
    workflow.add_edge(START, "router")
    workflow.add_conditional_edges(
        "router", choose_path, {"knowledge": "knowledge", "diagnose": "diagnose"}
    )
    workflow.add_edge("knowledge", "answer")
    workflow.add_edge("diagnose", "answer")
    workflow.add_edge("answer", END)
    return workflow.compile()


graph = build_graph()
