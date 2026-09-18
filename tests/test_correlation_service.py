from schemas.correlation import CorrelationRequest
from schemas.finding import (
    Evidence,
    Location,
    RuntimeEvidence,
    SecurityFinding,
    StaticEvidence,
)
from services.correlation_service import correlate, validate_rescan


def _finding(finding_id: str, *, runtime: bool = False) -> SecurityFinding:
    return SecurityFinding(
        finding_id=finding_id,
        title="SQL injection in user lookup",
        type="sql_injection",
        severity="high",
        cwe=["CWE-89"],
        location=Location(file="app.py", line=42, function="get_user"),
        source_tools=["semgrep"] if not runtime else ["runtime-fuzzer"],
        static_evidence=(
            [StaticEvidence(tool="semgrep", evidence=Evidence(sink="cursor.execute"))]
            if not runtime
            else []
        ),
        runtime_evidence=(
            [
                RuntimeEvidence(
                    endpoint="/user",
                    evidence="mutated request caused a 500",
                    function="get_user",
                )
            ]
            if runtime
            else []
        ),
    )


def test_static_and_runtime_evidence_merge_and_prioritize():
    report = correlate(
        CorrelationRequest(findings=[_finding("S001"), _finding("R001", runtime=True)])
    )

    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.merged_finding_ids == ["S001", "R001"]
    assert finding.status == "CONFIRMED"
    assert finding.confidence == 1.0
    assert finding.explanation


def test_rescan_marks_fixed_and_new_findings():
    report = correlate(CorrelationRequest(findings=[_finding("S001")]))
    new_finding = _finding("NEW", runtime=True).model_copy(update={"type": "xss"})
    results = validate_rescan(
        report, [_finding("RESCANNED", runtime=True), new_finding]
    )

    assert [result.status for result in results] == ["PERSISTING", "NEW"]
