"""
Phase 3 — Evidence Correlation Engine.

Deterministic, rule-based V1: compares each normalized static
SecurityFinding against each piece of runtime evidence using a fixed
set of weighted signals, and merges runtime evidence into a finding
when the resulting score clears a (configurable) threshold.

Explicitly OUT of scope here (later pipeline phases): confidence
scoring, AI analysis, remediation/patch generation, runtime analysis
itself, database/AWS integration. This module only decides whether two
pieces of evidence likely describe the same underlying issue, and if
so, merges them onto one finding.
"""

import json
from pathlib import Path
from pydantic import BaseModel, Field

from schemas.correlation import DEFAULT_CORRELATION_THRESHOLD
from schemas.finding import Evidence, Location, RuntimeEvidence, SecurityFinding, StaticEvidence

MOCK_DATA_DIR = Path(__file__).resolve().parent.parent / "mock-data"

# Signal name -> (points, human-readable reason). Order here also fixes
# the order reasons are reported in.
SIGNALS: dict[str, tuple[int, str]] = {
    "type": (20, "same vulnerability type"),
    "function": (30, "same function"),
    "file": (10, "same file"),
    "endpoint": (40, "same endpoint"),
    "sink": (25, "same sink"),
    "runtime_match": (30, "runtime evidence matches affected function"),
}

MAX_SCORE = 100


# ---------------------------------------------------------------------------
# Attribute extraction — pulls comparable fields out of the *existing*
# SecurityFinding / StaticEvidence / RuntimeEvidence models rather than
# adding new ones. A finding's function/file can come either from its
# top-level `location` or from any of its nested `static_evidence`
# entries (whichever is populated).
# ---------------------------------------------------------------------------


def _static_function(finding: SecurityFinding) -> str | None:
    if finding.location and finding.location.function:
        return finding.location.function
    for ev in finding.static_evidence:
        if ev.location and ev.location.function:
            return ev.location.function
    return None


def _static_file(finding: SecurityFinding) -> str | None:
    if finding.location and finding.location.file:
        return finding.location.file
    for ev in finding.static_evidence:
        if ev.location and ev.location.file:
            return ev.location.file
    return None


def _static_sink(finding: SecurityFinding) -> str | None:
    for ev in finding.static_evidence:
        if ev.evidence and ev.evidence.sink:
            return ev.evidence.sink
    return None


def _static_endpoint(finding: SecurityFinding) -> str | None:
    # The Phase 2 schema has no endpoint concept on the static side
    # (static analysis reports file/line/function, not HTTP routes) —
    # there's nowhere to read one from yet. Kept as an explicit hook:
    # once route-mapping exists, wiring it in here is all that's
    # needed for the "same endpoint" signal to start firing.
    return None


def _normalize(value: str | None) -> str | None:
    return value.strip().lower() if value else None


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def _score_from_matches(matches: dict[str, bool]) -> tuple[int, list[str]]:
    """Pure scoring step: given which signals matched, sum their weights
    (capped at MAX_SCORE) and produce the matching human-readable
    reasons, in the fixed order defined by SIGNALS."""
    total = 0
    reasons: list[str] = []
    for key, (points, reason) in SIGNALS.items():
        if matches.get(key):
            total += points
            reasons.append(reason)
    return min(total, MAX_SCORE), reasons


def score_finding_against_runtime(
    finding: SecurityFinding, runtime: RuntimeEvidence
) -> tuple[int, list[str]]:
    """Compute the deterministic correlation score + reasons between one
    static finding and one runtime evidence entry."""
    static_type = _normalize(finding.type)
    runtime_type = _normalize(runtime.type)

    static_function = _normalize(_static_function(finding))
    runtime_function = _normalize(runtime.function)

    static_file = _normalize(_static_file(finding))
    runtime_file = None  # RuntimeEvidence carries no file field in Phase 2

    static_endpoint = _normalize(_static_endpoint(finding))
    runtime_endpoint = _normalize(runtime.endpoint)

    static_sink = _normalize(_static_sink(finding))
    runtime_sink = None  # RuntimeEvidence carries no sink field in Phase 2

    function_match = bool(
        static_function and runtime_function and static_function == runtime_function
    )
    endpoint_match = bool(
        static_endpoint and runtime_endpoint and static_endpoint == runtime_endpoint
    )

    matches = {
        "type": bool(static_type and runtime_type and static_type == runtime_type),
        "function": function_match,
        "file": bool(static_file and runtime_file and static_file == runtime_file),
        "endpoint": endpoint_match,
        "sink": bool(static_sink and runtime_sink and static_sink == runtime_sink),
        # Signal 6 per spec: "runtime evidence exists for the same
        # function/endpoint" — a confirmation bonus on top of 2/4 when
        # dynamic testing actually observed something there, as
        # opposed to only static analysis having flagged it.
        "runtime_match": function_match or endpoint_match,
    }

    return _score_from_matches(matches)


# ---------------------------------------------------------------------------
# Correlation + merge
# ---------------------------------------------------------------------------


def _runtime_evidence_already_present(finding: SecurityFinding, runtime: RuntimeEvidence) -> bool:
    return any(existing == runtime for existing in finding.runtime_evidence)


def correlate(
    static_findings: list[SecurityFinding],
    runtime_evidence: list[RuntimeEvidence],
    threshold: float = DEFAULT_CORRELATION_THRESHOLD,
) -> tuple[list[SecurityFinding], list[dict]]:
    """
    Compare every (static finding, runtime evidence) pair, and merge
    runtime evidence into a finding wherever the score clears `threshold`.

    Returns (updated_findings, correlation_entries):
    - updated_findings: new SecurityFinding instances (inputs are never
      mutated), same order and count as `static_findings`, with
      correlated runtime evidence appended in-place onto the matching
      finding — no duplicate findings are ever created by correlation.
    - correlation_entries: one dict per (static finding, runtime
      evidence) pair considered, matching CorrelationEntry's fields.
    """
    updated = [f.model_copy(deep=True) for f in static_findings]
    entries: list[dict] = []

    for finding in updated:
        for idx, runtime in enumerate(runtime_evidence):
            score, reasons = score_finding_against_runtime(finding, runtime)
            correlated = score >= threshold

            entries.append(
                {
                    "static_finding_id": finding.finding_id,
                    "runtime_index": idx,
                    "score": score,
                    "correlated": correlated,
                    "reasons": reasons,
                }
            )

            if correlated and not _runtime_evidence_already_present(finding, runtime):
                finding.runtime_evidence.append(runtime)

    return updated, entries


# ---------------------------------------------------------------------------
# Mock-data adapters — turn the raw mock-data/*.json fixtures into
# normalized SecurityFinding / RuntimeEvidence objects so the correlation
# engine (and its demo endpoint / tests) can run against them directly.
# ---------------------------------------------------------------------------


def _title_from_type_and_function(vuln_type: str, function: str | None) -> str:
    label = vuln_type.replace("_", " ").title()
    return f"{label} in {function}" if function else label


def load_mock_static_findings(path: Path | None = None) -> list[SecurityFinding]:
    """Load mock-data/static.json and adapt its raw shape into normalized
    SecurityFinding objects (each carrying one StaticEvidence entry)."""
    file_path = path or (MOCK_DATA_DIR / "static.json")
    raw = json.loads(file_path.read_text())

    findings: list[SecurityFinding] = []
    for item in raw.get("findings", []):
        location = Location(
            file=item["file"], line=item.get("line"), function=item.get("function")
        )
        evidence = Evidence(
            source=item.get("source"),
            sink=item.get("sink"),
            flow=item.get("flow", []),
        )
        tools = item.get("tools", [])
        cwe = item.get("cwe")

        findings.append(
            SecurityFinding(
                finding_id=item["id"],
                title=_title_from_type_and_function(item["type"], item.get("function")),
                type=item["type"],
                severity=item.get("severity", "UNKNOWN"),
                cwe=[cwe] if isinstance(cwe, str) else list(cwe or []),
                location=location,
                static_evidence=[
                    StaticEvidence(
                        tool=tools[0] if tools else "unknown",
                        location=location,
                        evidence=evidence,
                    )
                ],
                source_tools=tools,
            )
        )
    return findings


def load_mock_runtime_evidence(path: Path | None = None) -> list[RuntimeEvidence]:
    """Load mock-data/runtime.json and adapt its raw shape into normalized
    RuntimeEvidence objects."""
    file_path = path or (MOCK_DATA_DIR / "runtime.json")
    raw = json.loads(file_path.read_text())

    return [
        RuntimeEvidence(
            endpoint=item["endpoint"],
            baseline_status=item.get("baseline_status"),
            mutated_status=item.get("mutated_status"),
            evidence=item.get("evidence", ""),
            function=item.get("function"),
            type=item.get("type"),
        )
        for item in raw.get("anomalies", [])
    ]