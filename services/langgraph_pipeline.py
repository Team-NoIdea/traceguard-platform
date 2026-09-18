"""Bounded LangGraph workflow for feedback-driven finding analysis.

The graph orchestrates deterministic correlation and optional model research;
it does not expose or depend on hidden chain-of-thought.
"""

from __future__ import annotations

from typing import TypedDict, Callable
from schemas.finding import SecurityFinding

from schemas.correlation import CorrelationRequest, FinalSecurityReport
from services.correlation_service import correlate

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - exercised only before optional install
    END = START = StateGraph = None


class WorkflowState(TypedDict, total=False):
    request: CorrelationRequest
    report: FinalSecurityReport
    feedback: list[str]
    research_round: int
    trace: list[str]
    researcher: Callable | None
    context_provider: Callable | None


def _correlate_node(state: WorkflowState) -> WorkflowState:
    report = correlate(state["request"], context_provider=state.get("context_provider"))
    return {
        "report": report,
        "feedback": list(state["request"].feedback),
        "research_round": 0,
        "trace": ["correlate: merged evidence and calculated confidence"],
    }


def _review_node(state: WorkflowState) -> WorkflowState:
    report = state["report"]
    feedback = list(state.get("feedback", []))
    for finding in report.findings:
        if finding.confidence is not None and finding.confidence < 0.6:
            feedback.append(
                f"{finding.finding_id}: confidence is below the review threshold"
            )
        if not finding.static_evidence and not finding.runtime_evidence:
            feedback.append(
                f"{finding.finding_id}: no supporting scanner evidence was supplied"
            )
        if finding.patch and finding.patch.unified_diff is None:
            feedback.append(
                f"{finding.finding_id}: no repository-context patch was produced"
            )
    return {
        "feedback": sorted(set(feedback)),
        "trace": state["trace"] + ["review: identified evidence gaps"],
    }


def _should_research(state: WorkflowState) -> str:
    request = state["request"]
    rounds = state.get("research_round", 0)
    has_feedback = bool(state.get("feedback"))
    if request.research_again and has_feedback and rounds < request.max_research_rounds:
        return "research"
    return END


def _research_node(state: WorkflowState) -> WorkflowState:
    round_number = state.get("research_round", 0) + 1
    collector = state.get("researcher")
    if collector is None:
        return {"research_round": state["request"].max_research_rounds,
                "trace": state["trace"] + ["research: unavailable without a repository evidence collector"]}
    fresh = collector(state.get("feedback", []), round_number)
    findings = {f.finding_id:f for f in state["request"].findings}
    for finding in fresh:
        findings[finding.finding_id] = finding
    request = state["request"].model_copy(update={"findings":list(findings.values()),
        "feedback":state.get("feedback", []), "research_again":True})
    report = correlate(request, context_provider=state.get("context_provider"))
    return {"request":request, "report":report, "research_round":round_number,
            "trace":state["trace"] + [f"research: acquired {len(fresh)} scanner observations in pass {round_number}"]}


def build_workflow():
    """Build a fresh graph so concurrent requests never share mutable state."""
    if StateGraph is None:
        raise RuntimeError(
            "LangGraph is not installed; run pip install -r requirements.txt"
        )
    graph = StateGraph(WorkflowState)
    graph.add_node("correlate", _correlate_node)
    graph.add_node("review", _review_node)
    graph.add_node("research", _research_node)
    graph.add_edge(START, "correlate")
    graph.add_edge("correlate", "review")
    graph.add_conditional_edges(
        "review", _should_research, {"research": "research", END: END}
    )
    graph.add_edge("research", "review")
    return graph.compile()


def run_workflow(request: CorrelationRequest, *, researcher=None, context_provider=None) -> FinalSecurityReport:
    result = build_workflow().invoke({"request": request, "researcher":researcher, "context_provider":context_provider})
    report = result["report"]
    return report.model_copy(update={"workflow_trace": result.get("trace", [])})
