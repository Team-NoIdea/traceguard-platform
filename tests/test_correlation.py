"""
Tests for schemas/correlation.py + services/correlation_service.py — the
Phase 3 deterministic evidence correlation engine.

No FastAPI TestClient here (it needs httpx, which isn't a project
dependency); these exercise the service layer directly, which is where
all the actual logic lives — routes/correlation.py is a thin pass-through.
"""

from schemas.correlation import CorrelationRequest, DEFAULT_CORRELATION_THRESHOLD
from schemas.finding import Location, RuntimeEvidence, SecurityFinding
from services import correlation_service
from services.correlation_service import MAX_SCORE, SIGNALS, correlate, score_finding_against_runtime


def _make_static_finding(
    finding_id="S001",
    vuln_type="SQL_INJECTION",
    function="get_user",
    file="app.py",
) -> SecurityFinding:
    return SecurityFinding(
        finding_id=finding_id,
        title=f"{vuln_type} in {function}",
        type=vuln_type,
        severity="HIGH",
        location=Location(file=file, line=42, function=function),
    )


def _make_runtime_evidence(
    endpoint="/user",
    function="get_user",
    anomaly_type="SQL_INJECTION",
) -> RuntimeEvidence:
    return RuntimeEvidence(
        endpoint=endpoint,
        baseline_status=200,
        mutated_status=500,
        evidence="Unhandled exception",
        function=function,
        type=anomaly_type,
    )


# ---------------------------------------------------------------------------
# 1. Matching static + runtime evidence correlates
# ---------------------------------------------------------------------------


def test_matching_static_and_runtime_evidence_correlates():
    finding = _make_static_finding()
    runtime = _make_runtime_evidence()  # same function + same type

    score, reasons = score_finding_against_runtime(finding, runtime)

    # type(20) + function(30) + runtime_match(30) = 80
    assert score == 80
    assert reasons == [
        "same vulnerability type",
        "same function",
        "runtime evidence matches affected function",
    ]

    updated, entries = correlate([finding], [runtime])
    assert entries[0]["correlated"] is True
    assert entries[0]["score"] == 80


# ---------------------------------------------------------------------------
# 2. Unrelated function does not correlate
# ---------------------------------------------------------------------------


def test_unrelated_function_does_not_correlate():
    finding = _make_static_finding(function="get_user")
    runtime = _make_runtime_evidence(
        endpoint="/completely/unrelated", function="send_email", anomaly_type="TIMEOUT"
    )

    score, reasons = score_finding_against_runtime(finding, runtime)

    assert score == 0
    assert reasons == []

    updated, entries = correlate([finding], [runtime])
    assert entries[0]["correlated"] is False
    assert updated[0].runtime_evidence == []


# ---------------------------------------------------------------------------
# 3. Same function but different vulnerability type
# ---------------------------------------------------------------------------


def test_same_function_different_type_still_correlates_without_type_bonus():
    finding = _make_static_finding(vuln_type="SQL_INJECTION", function="get_user")
    runtime = _make_runtime_evidence(function="get_user", anomaly_type="SERVER_ERROR")

    score, reasons = score_finding_against_runtime(finding, runtime)

    # function(30) + runtime_match(30) = 60 — no type bonus this time.
    assert score == 60
    assert "same vulnerability type" not in reasons
    assert "same function" in reasons
    assert "runtime evidence matches affected function" in reasons

    # Still correlated at the default threshold (50), just with a lower
    # score than the matching-type case above (80).
    updated, entries = correlate([finding], [runtime])
    assert entries[0]["correlated"] is True
    assert entries[0]["score"] == 60


# ---------------------------------------------------------------------------
# 4. Score never exceeds 100
# ---------------------------------------------------------------------------


def test_score_is_capped_at_100_even_if_all_signals_match():
    # Pure scoring-math test: sum of every signal's weight is
    # 20+30+10+40+25+30 = 155, which must be capped at MAX_SCORE (100).
    all_matched = {key: True for key in SIGNALS}
    score, reasons = correlation_service._score_from_matches(all_matched)

    assert score == MAX_SCORE
    assert score <= 100
    assert len(reasons) == len(SIGNALS)


def test_score_from_matches_never_exceeds_100_for_any_subset():
    # Cheap exhaustive-ish check across all 2^6 combinations of signals.
    keys = list(SIGNALS)
    for mask in range(2 ** len(keys)):
        matches = {k: bool(mask & (1 << i)) for i, k in enumerate(keys)}
        score, _ = correlation_service._score_from_matches(matches)
        assert 0 <= score <= 100


# ---------------------------------------------------------------------------
# 5. Reasons are returned
# ---------------------------------------------------------------------------


def test_reasons_are_human_readable_strings():
    finding = _make_static_finding()
    runtime = _make_runtime_evidence()

    _, reasons = score_finding_against_runtime(finding, runtime)

    assert isinstance(reasons, list)
    assert len(reasons) > 0
    assert all(isinstance(r, str) and r for r in reasons)


# ---------------------------------------------------------------------------
# 6. Runtime evidence is merged into the correlated finding
# ---------------------------------------------------------------------------


def test_runtime_evidence_is_merged_into_finding():
    finding = _make_static_finding()
    runtime = _make_runtime_evidence()

    updated, _ = correlate([finding], [runtime])

    merged = updated[0]
    assert len(merged.runtime_evidence) == 1
    assert merged.runtime_evidence[0] == runtime

    # The original input object must not be mutated.
    assert finding.runtime_evidence == []


# ---------------------------------------------------------------------------
# 7. Duplicate evidence is not created
# ---------------------------------------------------------------------------


def test_duplicate_runtime_evidence_is_not_added_twice():
    finding = _make_static_finding()
    runtime = _make_runtime_evidence()

    # First pass: merges the evidence in.
    first_pass, _ = correlate([finding], [runtime])
    assert len(first_pass[0].runtime_evidence) == 1

    # Re-running correlation on the already-merged finding against the
    # same runtime evidence pool must not duplicate it.
    second_pass, _ = correlate(first_pass, [runtime])
    assert len(second_pass[0].runtime_evidence) == 1
    assert second_pass[0].runtime_evidence[0] == runtime


def test_no_duplicate_findings_are_created():
    finding = _make_static_finding()
    runtime = _make_runtime_evidence()

    updated, _ = correlate([finding], [runtime])

    # One input finding in, exactly one finding out — correlation merges
    # onto the existing finding rather than appending a new one.
    assert len(updated) == 1
    assert updated[0].finding_id == finding.finding_id


# ---------------------------------------------------------------------------
# 8. Multiple static findings can be processed
# ---------------------------------------------------------------------------


def test_multiple_static_findings_are_each_processed_independently():
    finding_a = _make_static_finding(finding_id="S001", function="get_user", file="app.py")
    finding_b = _make_static_finding(
        finding_id="S002", vuln_type="XSS", function="render_comment", file="views.py"
    )

    runtime_a = _make_runtime_evidence(
        endpoint="/user", function="get_user", anomaly_type="SQL_INJECTION"
    )
    runtime_b = _make_runtime_evidence(
        endpoint="/comments", function="render_comment", anomaly_type="XSS"
    )

    updated, entries = correlate([finding_a, finding_b], [runtime_a, runtime_b])

    # 2 findings x 2 runtime evidence = 4 pairwise entries considered.
    assert len(entries) == 4
    assert len(updated) == 2

    by_id = {f.finding_id: f for f in updated}
    assert by_id["S001"].runtime_evidence == [runtime_a]
    assert by_id["S002"].runtime_evidence == [runtime_b]

    # Cross pairs (S001 x runtime_b, S002 x runtime_a) must not correlate.
    cross_entries = [
        e
        for e in entries
        if (e["static_finding_id"], e["runtime_index"]) in {("S001", 1), ("S002", 0)}
    ]
    assert all(e["correlated"] is False for e in cross_entries)


# ---------------------------------------------------------------------------
# 9. Empty inputs behave correctly
# ---------------------------------------------------------------------------


def test_empty_static_and_runtime_inputs():
    updated, entries = correlate([], [])
    assert updated == []
    assert entries == []


def test_empty_runtime_evidence_leaves_findings_unchanged():
    finding = _make_static_finding()
    updated, entries = correlate([finding], [])

    assert len(updated) == 1
    assert updated[0].runtime_evidence == []
    assert entries == []


def test_empty_static_findings_with_runtime_evidence_present():
    runtime = _make_runtime_evidence()
    updated, entries = correlate([], [runtime])

    assert updated == []
    assert entries == []  # nothing to pair the runtime evidence against


# ---------------------------------------------------------------------------
# Schema-level checks
# ---------------------------------------------------------------------------


def test_correlation_request_defaults():
    request = CorrelationRequest()
    assert request.static_findings == []
    assert request.runtime_evidence == []
    assert request.threshold == DEFAULT_CORRELATION_THRESHOLD == 50.0


def test_custom_threshold_changes_correlation_outcome():
    finding = _make_static_finding(vuln_type="SQL_INJECTION", function="get_user")
    runtime = _make_runtime_evidence(function="get_user", anomaly_type="SERVER_ERROR")
    # Score for this pair is 60 (see test 3 above).

    _, low_threshold_entries = correlate([finding], [runtime], threshold=50)
    assert low_threshold_entries[0]["correlated"] is True

    _, high_threshold_entries = correlate([finding], [runtime], threshold=70)
    assert high_threshold_entries[0]["correlated"] is False


# ---------------------------------------------------------------------------
# Mock-data integration
# ---------------------------------------------------------------------------


def test_mock_data_loaders_produce_valid_models():
    findings = correlation_service.load_mock_static_findings()
    runtime_evidence = correlation_service.load_mock_runtime_evidence()

    assert len(findings) == 1
    assert findings[0].finding_id == "S001"
    assert findings[0].type == "SQL_INJECTION"
    assert findings[0].location.function == "get_user"
    assert findings[0].cwe == ["CWE-89"]

    assert len(runtime_evidence) == 1
    assert runtime_evidence[0].endpoint == "/user"
    assert runtime_evidence[0].function == "get_user"
    assert runtime_evidence[0].type == "SERVER_ERROR"


def test_correlate_bundled_mock_data_end_to_end():
    findings = correlation_service.load_mock_static_findings()
    runtime_evidence = correlation_service.load_mock_runtime_evidence()

    updated, entries = correlate(findings, runtime_evidence)

    assert len(entries) == 1
    entry = entries[0]
    assert entry["static_finding_id"] == "S001"
    assert entry["runtime_index"] == 0
    # Same function (get_user) but different type (SQL_INJECTION vs
    # SERVER_ERROR) in the real mock data: 30 + 30 = 60.
    assert entry["score"] == 60
    assert entry["correlated"] is True

    assert updated[0].runtime_evidence[0].endpoint == "/user"