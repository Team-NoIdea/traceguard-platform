"""Contracts for the evidence-correlation and remediation pipeline."""

from typing import Literal

from pydantic import BaseModel, Field

from schemas.finding import RuntimeEvidence, SecurityFinding

DEFAULT_CORRELATION_THRESHOLD = 50.0


class CorrelationRequest(BaseModel):
    """Normalized findings from the static and runtime analysis stages."""

    findings: list[SecurityFinding] = Field(default_factory=list)
    static_findings: list[SecurityFinding] = Field(default_factory=list)
    runtime_evidence: list[RuntimeEvidence] = Field(default_factory=list)
    threshold: float = Field(default=50.0, ge=0.0, le=100.0)
    research_again: bool = False
    generate_patches: bool = False
    feedback: list[str] = Field(default_factory=list)
    max_research_rounds: int = Field(default=1, ge=0, le=2)


class PatchSuggestion(BaseModel):
    """A reviewable patch proposal. Applying patches is deliberately separate."""

    file: str
    rationale: str
    unified_diff: str | None = None
    regression_test: str | None = None
    validation_status: Literal["NOT_RUN", "VALID", "INVALID"] = "NOT_RUN"


class ValidationResult(BaseModel):
    """Result of comparing a post-fix rescan with the original report."""

    finding_id: str
    status: Literal["FIXED", "PERSISTING", "NEW", "NOT_RESCANNED"]
    details: str


class PrioritizedFinding(SecurityFinding):
    """A merged finding enriched with explainable prioritization metadata."""

    priority_score: float = Field(ge=0.0, le=100.0)
    correlation_key: str
    merged_finding_ids: list[str] = Field(default_factory=list)
    research_performed: bool = False
    patch: PatchSuggestion | None = None


class FinalSecurityReport(BaseModel):
    """Stable output of Person 3's pipeline."""

    findings: list[PrioritizedFinding] = Field(default_factory=list)
    validation: list[ValidationResult] = Field(default_factory=list)
    llm_provider: str = "deterministic"
    llm_error: str | None = None
    workflow_trace: list[str] = Field(default_factory=list)


class CorrelationEntry(BaseModel):
    static_finding_id: str
    runtime_index: int
    score: int = Field(ge=0, le=100)
    correlated: bool
    reasons: list[str] = Field(default_factory=list)


class CorrelationResponse(BaseModel):
    findings: list[SecurityFinding] = Field(default_factory=list)
    correlations: list[CorrelationEntry] = Field(default_factory=list)
