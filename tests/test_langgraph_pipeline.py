from schemas.correlation import CorrelationRequest
from schemas.finding import SecurityFinding
from services.langgraph_pipeline import run_workflow


def test_feedback_workflow_stops_at_research_limit():
    report = run_workflow(
        CorrelationRequest(
            findings=[
                SecurityFinding(
                    finding_id="F001",
                    title="Possible injection",
                    type="sql_injection",
                    severity="high",
                )
            ],
            research_again=True,
            max_research_rounds=1,
            feedback=["Review this finding again"],
        )
    )

    assert report.findings[0].confidence == 0.25
    assert report.workflow_trace == [
        "correlate: merged evidence and calculated confidence",
        "review: identified evidence gaps",
        "research: unavailable without a repository evidence collector",
        "review: identified evidence gaps",
    ]
