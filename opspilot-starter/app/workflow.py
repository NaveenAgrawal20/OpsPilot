"""Small LangGraph workflow: classify -> retrieve -> explain.

A2A delegation is intentionally a Day 5 milestone, not faked here.
"""

import os
from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from .knowledge import format_citations, search_docs
from .llm import generate_answer


class AgentState(TypedDict, total=False):
    question: str
    intent: str
    sources: list[dict]
    answer: str


def classify(state: AgentState) -> dict:
    question = state["question"].lower()
    keywords = ("crash", "error", "failing", "oomkilled", "restart", "imagepull")
    intent = "diagnose" if any(word in question for word in keywords) else "knowledge"
    return {"intent": intent}


def retrieve(state: AgentState) -> dict:
    return {"sources": search_docs(state["question"])}


def explain(state: AgentState) -> dict:
    sources = state["sources"]
    if not sources:
        return {"answer": "No relevant documentation found. Please provide more details."}
    if not os.getenv("OPENROUTER_API_KEY") or not os.getenv("OPENROUTER_MODEL"):
        # Offline fallback is a retrieval preview, not a simulated LLM answer.
        titles = ", ".join(source["title"] for source in sources)
        answer = f"Retrieved evidence (LLM not configured): {titles}"
    else:
        answer = generate_answer(state["question"], sources)
    return {"answer": answer + format_citations(sources)}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("classify", classify)
    graph.add_node("retrieve", retrieve)
    graph.add_node("explain", explain)
    graph.add_edge(START, "classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "explain")
    graph.add_edge("explain", END)
    return graph.compile()


graph = build_graph()
