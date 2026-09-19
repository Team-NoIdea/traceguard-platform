"""
Phase 3 — Evidence Correlation Engine: request/response models.

Reuses the Phase 2 normalized models (SecurityFinding, RuntimeEvidence)
rather than duplicating them — this module only adds the shapes needed
to describe a correlation *request* and *result*. No new finding-level
fields are introduced here.
"""

from pydantic import BaseModel, Field

from schemas.finding import RuntimeEvidence, SecurityFinding

DEFAULT_CORRELATION_THRESHOLD = 50.0


class CorrelationRequest(BaseModel):
    """Input to the correlation engine: normalized static findings plus a
    pool of runtime evidence to try to correlate against them."""

    static_findings: list[SecurityFinding] = Field(default_factory=list)
    runtime_evidence: list[RuntimeEvidence] = Field(default_factory=list)
    threshold: float = Field(
        default=DEFAULT_CORRELATION_THRESHOLD,
        ge=0.0,
        le=100.0,
    )


class CorrelationEntry(BaseModel):
    """One static-finding <-> runtime-evidence comparison result."""

    static_finding_id: str
    runtime_index: int
    score: int = Field(ge=0, le=100)
    correlated: bool
    reasons: list[str] = Field(default_factory=list)


class CorrelationResponse(BaseModel):
    """Findings (merged where correlated) plus the full correlation ledger.

    `findings` mirrors the input static findings 1:1, in the same order,
    with correlated runtime evidence merged in — no new/duplicate
    findings are created by correlation.
    """

    findings: list[SecurityFinding] = Field(default_factory=list)
    correlations: list[CorrelationEntry] = Field(default_factory=list)