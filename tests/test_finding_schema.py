"""
Tests for schemas/finding.py — the normalized security finding schema
(Phase 2). Pure schema/validation tests: no routes, services, or I/O.
"""

import pytest
from pydantic import ValidationError

from schemas.finding import (
    Evidence,
    FindingsResponse,
    Location,
    RuntimeEvidence,
    SecurityFinding,
    StaticEvidence,
)


# ---------------------------------------------------------------------------
# Valid finding creation
# ---------------------------------------------------------------------------


def test_minimal_valid_finding():
    """Only the required fields are supplied; everything else should default."""
    finding = SecurityFinding(
        finding_id="F-001",
        title="SQL Injection in login handler",
        type="sql_injection",
        severity="high",
    )

    assert finding.finding_id == "F-001"
    assert finding.title == "SQL Injection in login handler"
    assert finding.type == "sql_injection"
    assert finding.severity == "high"
    assert finding.status == "OPEN"
    assert finding.location is None
    assert finding.confidence is None
    assert finding.explanation is None
    assert finding.remediation is None


def test_full_valid_finding_round_trip():
    """A fully populated finding, including nested evidence, validates and
    round-trips through model_dump()/model_validate() unchanged."""
    finding = SecurityFinding(
        finding_id="F-002",
        title="Command injection via subprocess",
        type="command_injection",
        severity="critical",
        cwe=["CWE-78"],
        location=Location(file="app/utils.py", line=42, function="run_cmd"),
        confidence=0.87,
        static_evidence=[
            StaticEvidence(
                tool="semgrep",
                rule_id="python.lang.security.subprocess-shell-true",
                location=Location(file="app/utils.py", line=42),
                evidence=Evidence(
                    source="request.args",
                    sink="subprocess.call",
                    flow=["request.args", "cmd", "subprocess.call"],
                    description="Untrusted input reaches a shell call",
                ),
            )
        ],
        runtime_evidence=[
            RuntimeEvidence(
                endpoint="/api/run",
                method="POST",
                baseline_status=200,
                mutated_status=500,
                evidence="Mutated payload caused a 500 with a stack trace leak",
                function="run_cmd",
            )
        ],
        source_tools=["semgrep", "runtime-fuzzer"],
        status="CONFIRMED",
        explanation="Untrusted request data reaches subprocess.call with shell=True.",
        remediation="Use subprocess.run with a list of args and shell=False.",
    )

    dumped = finding.model_dump()
    rebuilt = SecurityFinding.model_validate(dumped)
    assert rebuilt == finding
    assert dumped["cwe"] == ["CWE-78"]
    assert dumped["confidence"] == 0.87


# ---------------------------------------------------------------------------
# Nested evidence
# ---------------------------------------------------------------------------


def test_nested_static_evidence():
    finding = SecurityFinding(
        finding_id="F-003",
        title="Hardcoded secret",
        type="secret_exposure",
        severity="medium",
        static_evidence=[
            StaticEvidence(
                tool="codeql",
                rule_id="py/hardcoded-credentials",
                location=Location(file="config.py", line=10, function=None),
                evidence=Evidence(description="API key literal found in source"),
            ),
            StaticEvidence(tool="joern"),  # only the required field
        ],
    )

    assert len(finding.static_evidence) == 2

    first = finding.static_evidence[0]
    assert first.tool == "codeql"
    assert first.rule_id == "py/hardcoded-credentials"
    assert first.location.file == "config.py"
    assert first.location.line == 10
    assert first.evidence.description == "API key literal found in source"

    second = finding.static_evidence[1]
    assert second.tool == "joern"
    assert second.rule_id is None
    assert second.location is None
    assert second.evidence is None


def test_nested_runtime_evidence():
    finding = SecurityFinding(
        finding_id="F-004",
        title="Auth bypass on admin endpoint",
        type="broken_access_control",
        severity="high",
        runtime_evidence=[
            RuntimeEvidence(
                endpoint="/admin/users",
                method="GET",
                baseline_status=401,
                mutated_status=200,
                evidence="Removing the Authorization header still returned 200",
            )
        ],
    )

    assert len(finding.runtime_evidence) == 1
    ev = finding.runtime_evidence[0]
    assert ev.endpoint == "/admin/users"
    assert ev.method == "GET"
    assert ev.baseline_status == 401
    assert ev.mutated_status == 200
    assert ev.evidence == "Removing the Authorization header still returned 200"
    assert ev.function is None


def test_runtime_evidence_accepts_and_preserves_optional_type():
    """RuntimeEvidence gained an optional `type` field in Phase 3 (used by
    the correlation engine to compare against a static finding's
    vulnerability type). Confirm it's accepted and round-trips."""
    evidence = RuntimeEvidence(
        endpoint="/user",
        evidence="Unhandled exception",
        type="SERVER_ERROR",
    )

    assert evidence.type == "SERVER_ERROR"


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


def test_default_empty_lists():
    finding = SecurityFinding(
        finding_id="F-005",
        title="Untitled finding",
        type="misc",
        severity="low",
    )

    assert finding.cwe == []
    assert finding.static_evidence == []
    assert finding.runtime_evidence == []
    assert finding.source_tools == []

    # Each finding's default list must be its own instance, not a shared
    # mutable default across models (the classic Python pitfall that
    # Field(default_factory=list) exists to avoid).
    other = SecurityFinding(
        finding_id="F-006",
        title="Another finding",
        type="misc",
        severity="low",
    )
    finding.cwe.append("CWE-79")
    assert other.cwe == []


def test_evidence_default_flow_list():
    ev = Evidence()
    assert ev.flow == []
    assert ev.source is None
    assert ev.sink is None
    assert ev.description is None


def test_findings_response_default_list():
    response = FindingsResponse()
    assert response.findings == []

    response_with_data = FindingsResponse(
        findings=[
            SecurityFinding(
                finding_id="F-007",
                title="XSS in comment field",
                type="xss",
                severity="medium",
            )
        ]
    )
    assert len(response_with_data.findings) == 1
    assert response_with_data.findings[0].finding_id == "F-007"


# ---------------------------------------------------------------------------
# Validation failures
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bad_confidence", [-0.01, -1.0, 1.01, 2.0])
def test_confidence_out_of_range_fails(bad_confidence):
    with pytest.raises(ValidationError):
        SecurityFinding(
            finding_id="F-008",
            title="Bad confidence",
            type="misc",
            severity="low",
            confidence=bad_confidence,
        )


@pytest.mark.parametrize("edge_confidence", [0.0, 1.0])
def test_confidence_at_boundaries_is_valid(edge_confidence):
    finding = SecurityFinding(
        finding_id="F-009",
        title="Boundary confidence",
        type="misc",
        severity="low",
        confidence=edge_confidence,
    )
    assert finding.confidence == edge_confidence


@pytest.mark.parametrize(
    "missing_field", ["finding_id", "title", "type", "severity"]
)
def test_missing_required_field_on_finding_fails(missing_field):
    payload = {
        "finding_id": "F-010",
        "title": "Missing field test",
        "type": "misc",
        "severity": "low",
    }
    del payload[missing_field]

    with pytest.raises(ValidationError):
        SecurityFinding(**payload)


def test_missing_required_field_on_location_fails():
    with pytest.raises(ValidationError):
        Location()  # `file` is required


def test_missing_required_field_on_static_evidence_fails():
    with pytest.raises(ValidationError):
        StaticEvidence()  # `tool` is required


def test_missing_required_fields_on_runtime_evidence_fails():
    with pytest.raises(ValidationError):
        RuntimeEvidence(endpoint="/api/x")  # `evidence` is required too