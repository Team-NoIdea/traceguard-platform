"""
Phase 2 — Normalized Security Finding Schema.

This module defines the common shape that findings from *any* upstream
engine (Semgrep, CodeQL, Joern static analysis, or runtime/fuzz testing)
get normalized into before evidence correlation, confidence scoring, or
AI analysis touch them.

Scope note: this file only defines the schema. It does not implement
correlation, confidence scoring, AI analysis, remediation, or runtime
analysis logic — those are later pipeline stages.
"""

from pydantic import BaseModel, Field


class Location(BaseModel):
    """A place in source code a finding is anchored to."""

    file: str
    line: int | None = None
    function: str | None = None


class Evidence(BaseModel):
    """Generic source/sink taint-flow evidence for a finding."""

    source: str | None = None
    sink: str | None = None
    flow: list[str] = Field(default_factory=list)
    description: str | None = None


class StaticEvidence(BaseModel):
    """Evidence contributed by a static analysis engine (e.g. Semgrep, CodeQL, Joern)."""

    tool: str
    rule_id: str | None = None
    location: Location | None = None
    evidence: Evidence | None = None


class RuntimeEvidence(BaseModel):
    """Evidence contributed by runtime/dynamic testing (e.g. baseline vs. mutated request behavior)."""

    endpoint: str
    method: str | None = None
    baseline_status: int | None = None
    mutated_status: int | None = None
    evidence: str
    function: str | None = None
    type: str | None = None
    """Category of the observed runtime anomaly (e.g. "SERVER_ERROR",
    "SQL_INJECTION"). Optional and additive: the raw runtime mock data
    already carries this under the same key. Used by the Phase 3
    correlation engine to compare against a static finding's
    vulnerability type."""


class SecurityFinding(BaseModel):
    """A single normalized security finding, merging static and/or runtime evidence."""

    finding_id: str
    title: str
    type: str
    severity: str
    cwe: list[str] = Field(default_factory=list)
    location: Location | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    static_evidence: list[StaticEvidence] = Field(default_factory=list)
    runtime_evidence: list[RuntimeEvidence] = Field(default_factory=list)
    source_tools: list[str] = Field(default_factory=list)
    status: str = "OPEN"
    explanation: str | None = None
    remediation: str | None = None


class FindingsResponse(BaseModel):
    """Envelope for returning a collection of findings from an endpoint."""

    findings: list[SecurityFinding] = Field(default_factory=list)