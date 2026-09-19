"""
Tests for services/confidence.py — the Phase 4 deterministic confidence
scoring engine.

No FastAPI/TestClient here — this is a pure service-layer module with no
route yet (none was requested for Phase 4), so tests exercise
score_finding()/apply_confidence() directly.
"""

from schemas.finding import Evidence, Location, RuntimeEvidence, SecurityFinding, StaticEvidence
from services.confidence import (
    BASE_CONFIDENCE,
    MAX_CONFIDENCE,
    MULTIPLE_TOOLS_BONUS,
    RUNTIME_CONFIRMATION_BONUS,
    SOURCE_TO_SINK_FLOW_BONUS,
    STATIC_EVIDENCE_BONUS,
    STRONG_CORRELATION_BONUS,
    apply_confidence,
    score_finding,
)


def _minimal_finding(**overrides) -> SecurityFinding:
    defaults = dict(
        finding_id="F-100",
        title="Test finding",
        type="SQL_INJECTION",
        severity="HIGH",
    )
    defaults.update(overrides)
    return SecurityFinding(**defaults)


# ---------------------------------------------------------------------------
# Empty / minimal finding
# ---------------------------------------------------------------------------


def test_empty_minimal_finding_gets_only_the_base_score():
    finding = _minimal_finding()

    result = score_finding(finding)

    assert result.confidence == BASE_CONFIDENCE
    assert result.raw_score == BASE_CONFIDENCE
    assert result.contributions == {}
    assert len(result.reasons) == 1
    assert "baseline" in result.reasons[0]


# ---------------------------------------------------------------------------
# Static-only finding
# ---------------------------------------------------------------------------


def test_static_only_finding():
    finding = _minimal_finding(
        location=Location(file="app.py", line=42, function="get_user"),
        static_evidence=[
            StaticEvidence(
                tool="semgrep",
                location=Location(file="app.py", line=42, function="get_user"),
                evidence=Evidence(description="tainted query"),
            )
        ],
    )

    result = score_finding(finding)

    expected = round(BASE_CONFIDENCE + STATIC_EVIDENCE_BONUS, 2)
    assert result.confidence == expected
    assert result.contributions == {"static_evidence": STATIC_EVIDENCE_BONUS}
    assert "runtime_confirmation" not in result.contributions


# ---------------------------------------------------------------------------
# Static + runtime finding (no function agreement -> no correlation bonus)
# ---------------------------------------------------------------------------


def test_static_and_runtime_finding_without_function_agreement():
    finding = _minimal_finding(
        location=Location(file="app.py", function="get_user"),
        static_evidence=[
            StaticEvidence(tool="semgrep", evidence=Evidence(description="tainted query"))
        ],
        runtime_evidence=[
            RuntimeEvidence(
                endpoint="/other",
                evidence="unrelated anomaly",
                function="some_other_function",
            )
        ],
    )

    result = score_finding(finding)

    expected = round(BASE_CONFIDENCE + STATIC_EVIDENCE_BONUS + RUNTIME_CONFIRMATION_BONUS, 2)
    assert result.confidence == expected
    assert result.contributions == {
        "static_evidence": STATIC_EVIDENCE_BONUS,
        "runtime_confirmation": RUNTIME_CONFIRMATION_BONUS,
    }
    # Runtime evidence exists, but for a different function -> no
    # "strong correlation" bonus.
    assert "strong_function_correlation" not in result.contributions


# ---------------------------------------------------------------------------
# Source-to-sink evidence
# ---------------------------------------------------------------------------


def test_source_to_sink_flow_via_explicit_source_and_sink():
    finding = _minimal_finding(
        static_evidence=[
            StaticEvidence(
                tool="semgrep",
                evidence=Evidence(source="request.args", sink="cursor.execute"),
            )
        ],
    )

    result = score_finding(finding)

    assert "source_to_sink_flow" in result.contributions
    assert result.contributions["source_to_sink_flow"] == SOURCE_TO_SINK_FLOW_BONUS


def test_source_to_sink_flow_via_flow_chain():
    finding = _minimal_finding(
        static_evidence=[
            StaticEvidence(
                tool="semgrep",
                evidence=Evidence(flow=["request.args", "user_id", "cursor.execute"]),
            )
        ],
    )

    result = score_finding(finding)

    assert "source_to_sink_flow" in result.contributions


def test_no_source_to_sink_flow_when_only_one_side_present():
    finding = _minimal_finding(
        static_evidence=[
            StaticEvidence(tool="semgrep", evidence=Evidence(source="request.args"))
        ],
    )

    result = score_finding(finding)

    assert "source_to_sink_flow" not in result.contributions


# ---------------------------------------------------------------------------
# Multiple independent tools
# ---------------------------------------------------------------------------


def test_multiple_independent_tools_agree():
    finding = _minimal_finding(
        static_evidence=[
            StaticEvidence(tool="semgrep"),
            StaticEvidence(tool="codeql"),
        ],
    )

    result = score_finding(finding)

    assert result.contributions["multiple_tools"] == MULTIPLE_TOOLS_BONUS


def test_single_tool_does_not_trigger_multi_tool_bonus():
    finding = _minimal_finding(static_evidence=[StaticEvidence(tool="semgrep")])

    result = score_finding(finding)

    assert "multiple_tools" not in result.contributions


def test_multiple_tools_dedupes_case_insensitively():
    # "semgrep" reported twice under different casing should NOT count
    # as two independent tools.
    finding = _minimal_finding(
        source_tools=["Semgrep"],
        static_evidence=[StaticEvidence(tool="semgrep")],
    )

    result = score_finding(finding)

    assert "multiple_tools" not in result.contributions


# ---------------------------------------------------------------------------
# Strong function/file correlation
# ---------------------------------------------------------------------------


def test_strong_function_correlation_when_static_and_runtime_agree():
    finding = _minimal_finding(
        location=Location(file="app.py", function="get_user"),
        static_evidence=[StaticEvidence(tool="semgrep")],
        runtime_evidence=[
            RuntimeEvidence(endpoint="/user", evidence="500 error", function="get_user")
        ],
    )

    result = score_finding(finding)

    assert result.contributions["strong_function_correlation"] == STRONG_CORRELATION_BONUS


def test_no_strong_correlation_when_functions_differ():
    finding = _minimal_finding(
        location=Location(file="app.py", function="get_user"),
        runtime_evidence=[
            RuntimeEvidence(endpoint="/other", evidence="500 error", function="delete_user")
        ],
    )

    result = score_finding(finding)

    assert "strong_function_correlation" not in result.contributions


# ---------------------------------------------------------------------------
# Score capped at 1.0
# ---------------------------------------------------------------------------


def test_score_is_capped_at_1_0_when_every_signal_fires():
    finding = _minimal_finding(
        location=Location(file="app.py", function="get_user"),
        source_tools=["semgrep"],
        static_evidence=[
            StaticEvidence(
                tool="codeql",  # distinct from source_tools -> multi-tool bonus
                location=Location(file="app.py", function="get_user"),
                evidence=Evidence(source="request.args", sink="cursor.execute"),
            )
        ],
        runtime_evidence=[
            RuntimeEvidence(endpoint="/user", evidence="500 error", function="get_user")
        ],
    )

    result = score_finding(finding)

    # base .4 + static .2 + runtime .2 + flow .1 + multi-tool .1 + correlation .1 = 1.1
    assert result.raw_score == 1.1
    assert result.confidence == MAX_CONFIDENCE
    assert result.confidence <= 1.0
    assert any("capped" in r for r in result.reasons)


def test_confidence_never_exceeds_1_0_for_any_combination():
    # Cheap sanity sweep: confidence must never exceed the cap regardless
    # of which subset of evidence is present.
    import itertools

    base_kwargs = dict(
        location=Location(file="app.py", function="get_user"),
    )
    evidence_options = {
        "static_evidence": [
            StaticEvidence(
                tool="codeql",
                evidence=Evidence(source="s", sink="k"),
            )
        ],
        "runtime_evidence": [
            RuntimeEvidence(endpoint="/user", evidence="err", function="get_user")
        ],
        "source_tools": ["semgrep"],
    }
    keys = list(evidence_options)
    for r in range(len(keys) + 1):
        for combo in itertools.combinations(keys, r):
            kwargs = {**base_kwargs, **{k: evidence_options[k] for k in combo}}
            finding = _minimal_finding(**kwargs)
            result = score_finding(finding)
            assert result.confidence <= 1.0


# ---------------------------------------------------------------------------
# Deterministic / repeatable scoring
# ---------------------------------------------------------------------------


def test_scoring_is_deterministic_for_the_same_object():
    finding = _minimal_finding(
        static_evidence=[StaticEvidence(tool="semgrep")],
        runtime_evidence=[
            RuntimeEvidence(endpoint="/user", evidence="err", function=None)
        ],
    )

    first = score_finding(finding)
    second = score_finding(finding)

    assert first.confidence == second.confidence
    assert first.contributions == second.contributions
    assert first.reasons == second.reasons


def test_scoring_is_deterministic_across_equal_but_distinct_objects():
    def build():
        return _minimal_finding(
            location=Location(file="app.py", function="get_user"),
            static_evidence=[StaticEvidence(tool="semgrep")],
            runtime_evidence=[
                RuntimeEvidence(endpoint="/user", evidence="err", function="get_user")
            ],
        )

    result_a = score_finding(build())
    result_b = score_finding(build())

    assert result_a.confidence == result_b.confidence
    assert result_a.contributions == result_b.contributions
    assert result_a.reasons == result_b.reasons


# ---------------------------------------------------------------------------
# Non-mutation + apply_confidence
# ---------------------------------------------------------------------------


def test_score_finding_does_not_mutate_the_input():
    finding = _minimal_finding(static_evidence=[StaticEvidence(tool="semgrep")])
    assert finding.confidence is None

    score_finding(finding)

    assert finding.confidence is None  # untouched


def test_apply_confidence_returns_a_new_finding_without_mutating_input():
    finding = _minimal_finding(static_evidence=[StaticEvidence(tool="semgrep")])

    updated = apply_confidence(finding)

    assert finding.confidence is None  # original untouched
    assert updated.confidence == round(BASE_CONFIDENCE + STATIC_EVIDENCE_BONUS, 2)
    assert updated is not finding
    assert updated.finding_id == finding.finding_id