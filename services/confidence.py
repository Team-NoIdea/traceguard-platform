"""
Phase 4 — Confidence Scoring.

Deterministic, rule-based V1: no ML. Confidence answers a different
question than severity does:

- Severity: "how bad would this be if it's real?" (set by the tool/rule
  that raised the finding, already on SecurityFinding.severity)
- Confidence: "how strongly does our collected evidence support that
  this finding IS real?" (computed here)

The score starts from a fixed baseline and adds fixed-point bonuses for
each independent piece of corroborating evidence found on the finding,
capped at 1.0. Every bonus that fires is recorded as a plain-English
reason, so the whole calculation can be read straight off the result
object during a demo — no hidden state, no model, nothing to retrain.

Explicitly OUT of scope here (later pipeline phases): ML-based scoring,
AI analysis, remediation/patch generation. This module only scores
evidence that already exists on a finding — it never fetches, generates,
or correlates new evidence itself (that's Phase 3's job).
"""

from dataclasses import dataclass, field

from schemas.finding import SecurityFinding

# --- Tunable weights -------------------------------------------------------
# Kept as named constants (not magic numbers) so the whole formula reads
# as a flat list during a presentation.

BASE_CONFIDENCE = 0.4          # every finding starts here — it was reported at all
STATIC_EVIDENCE_BONUS = 0.2    # at least one static analysis hit
RUNTIME_CONFIRMATION_BONUS = 0.2  # at least one runtime observation
SOURCE_TO_SINK_FLOW_BONUS = 0.1   # a concrete taint path was traced
MULTIPLE_TOOLS_BONUS = 0.1        # 2+ independent tools agree
STRONG_CORRELATION_BONUS = 0.1    # static + runtime evidence agree on the same function

MAX_CONFIDENCE = 1.0


@dataclass
class ConfidenceResult:
    """Structured, explainable output of scoring one SecurityFinding.

    `contributions` lists every signal considered with the points it
    actually contributed (0.0 if it didn't apply), in a fixed order, so
    the full arithmetic (base + contributions, capped) is visible at a
    glance. `reasons` is the same information as plain-English sentences
    for a demo or a UI.
    """

    finding_id: str
    confidence: float
    base_score: float
    raw_score: float  # pre-cap total; differs from `confidence` only when capped
    contributions: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Individual evidence checks. Each is a pure, read-only inspection of the
# finding — none of them mutate it. Function extraction mirrors Phase 3's
# precedence locally (see _static_function below) rather than importing
# from services/correlation_service, so this module has no dependency on
# Phase 3's internals.
# ---------------------------------------------------------------------------


def _static_function(finding: SecurityFinding) -> str | None:
    """Extract the finding's function name, same precedence Phase 3's
    correlation engine uses: top-level `finding.location.function` first,
    then the first populated `StaticEvidence.location.function`.

    Duplicated locally (rather than imported from
    services/correlation_service) so this module doesn't depend on
    Phase 3's private helpers — kept in sync by using the identical
    precedence, not by sharing code.
    """
    if finding.location and finding.location.function:
        return finding.location.function
    for ev in finding.static_evidence:
        if ev.location and ev.location.function:
            return ev.location.function
    return None


def _has_static_evidence(finding: SecurityFinding) -> bool:
    return bool(finding.static_evidence)


def _has_runtime_confirmation(finding: SecurityFinding) -> bool:
    return bool(finding.runtime_evidence)


def _has_source_to_sink_flow(finding: SecurityFinding) -> bool:
    """True if any static evidence entry traces a concrete taint path:
    either an explicit source+sink pair, or a populated flow chain."""
    for ev in finding.static_evidence:
        if not ev.evidence:
            continue
        if ev.evidence.source and ev.evidence.sink:
            return True
        if len(ev.evidence.flow) >= 2:
            return True
    return False


def _distinct_tools(finding: SecurityFinding) -> set[str]:
    """Independent tools that reported on this finding, combining
    `source_tools` and each static evidence entry's `tool` (case-folded
    so "Semgrep" and "semgrep" count as one)."""
    tools = {t.strip().lower() for t in finding.source_tools if t}
    tools |= {ev.tool.strip().lower() for ev in finding.static_evidence if ev.tool}
    return tools


def _has_multiple_independent_tools(finding: SecurityFinding) -> bool:
    return len(_distinct_tools(finding)) >= 2


def _has_strong_function_correlation(finding: SecurityFinding) -> bool:
    """True if a runtime evidence entry independently names the same
    function the static evidence/location points at — i.e. static and
    runtime evidence agree, not just both being present. Uses the same
    function-extraction precedence Phase 3's correlation engine uses
    (see `_static_function` above), so "agreement" here means the same
    thing it means during correlation.

    (File-level agreement isn't checkable yet: RuntimeEvidence has no
    `file` field in the current schema — see services/correlation_service.py.
    This only checks function; file is a documented no-op hook for when
    that field exists, matching the same gap Phase 3 already documented.)
    """
    static_function = _static_function(finding)
    if not static_function:
        return False
    static_function = static_function.strip().lower()

    for rt in finding.runtime_evidence:
        if rt.function and rt.function.strip().lower() == static_function:
            return True
    return False


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_finding(finding: SecurityFinding) -> ConfidenceResult:
    """Compute a deterministic confidence score for `finding`.

    Read-only: `finding` itself is never modified. Use `apply_confidence`
    if you want a new SecurityFinding with the result written onto it.
    """
    contributions: dict[str, float] = {}
    reasons: list[str] = [f"baseline confidence {BASE_CONFIDENCE:.2f} (a finding was reported)"]

    if _has_static_evidence(finding):
        contributions["static_evidence"] = STATIC_EVIDENCE_BONUS
        reasons.append(f"static analysis evidence present (+{STATIC_EVIDENCE_BONUS:.2f})")

    if _has_runtime_confirmation(finding):
        contributions["runtime_confirmation"] = RUNTIME_CONFIRMATION_BONUS
        reasons.append(f"runtime confirmation present (+{RUNTIME_CONFIRMATION_BONUS:.2f})")

    if _has_source_to_sink_flow(finding):
        contributions["source_to_sink_flow"] = SOURCE_TO_SINK_FLOW_BONUS
        reasons.append(f"source-to-sink flow traced (+{SOURCE_TO_SINK_FLOW_BONUS:.2f})")

    if _has_multiple_independent_tools(finding):
        contributions["multiple_tools"] = MULTIPLE_TOOLS_BONUS
        tools = ", ".join(sorted(_distinct_tools(finding)))
        reasons.append(f"multiple independent tools agree [{tools}] (+{MULTIPLE_TOOLS_BONUS:.2f})")

    if _has_strong_function_correlation(finding):
        contributions["strong_function_correlation"] = STRONG_CORRELATION_BONUS
        reasons.append(
            f"static and runtime evidence agree on the same function (+{STRONG_CORRELATION_BONUS:.2f})"
        )

    raw_score = round(BASE_CONFIDENCE + sum(contributions.values()), 2)
    confidence = min(raw_score, MAX_CONFIDENCE)

    if confidence < raw_score:
        reasons.append(f"raw score {raw_score:.2f} capped at {MAX_CONFIDENCE:.2f}")

    return ConfidenceResult(
        finding_id=finding.finding_id,
        confidence=confidence,
        base_score=BASE_CONFIDENCE,
        raw_score=raw_score,
        contributions=contributions,
        reasons=reasons,
    )


def apply_confidence(finding: SecurityFinding, result: ConfidenceResult | None = None) -> SecurityFinding:
    """Return a NEW SecurityFinding with `.confidence` set from scoring.

    `finding` is never mutated — this mirrors the established pattern in
    services/correlation_service.py (correlate() returns model_copy'd
    findings rather than modifying its inputs in place).
    """
    result = result or score_finding(finding)
    return finding.model_copy(update={"confidence": result.confidence})