"""Contracts for the isolated repository scan MVP."""

from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from schemas.correlation import FinalSecurityReport
from schemas.remediation import FixAttempt


class ScanRequest(BaseModel):
    repository_url: HttpUrl
    branch: str = Field(default="main", min_length=1, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9_./-]*$")
    runtime_enabled: bool = False
    runtime_entrypoint: str = Field(default="main:app", pattern=r"^[A-Za-z_][A-Za-z0-9_.]*:[A-Za-z_][A-Za-z0-9_]*$")
    research_again: bool = True
    max_research_rounds: int = Field(default=1, ge=0, le=2)
    authorized: bool = Field(
        default=False,
        description="Caller confirms they own or are authorized to test this repository.",
    )


class SensorResult(BaseModel):
    name: str
    status: Literal["COMPLETED", "SKIPPED", "FAILED"]
    detail: str
    finding_count: int = 0
    phase: str = "initial"
    image: str | None = None
    duration_seconds: float = 0


class DiscoveredRoute(BaseModel):
    method: str
    path: str
    function: str | None = None
    framework: str
    file: str | None = None
    line: int | None = None


class ScanResponse(BaseModel):
    scan_id: str
    repository_url: str
    branch: str
    status: Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED"] = "COMPLETED"
    commit_sha: str | None = None
    runtime_enabled: bool = False
    runtime_entrypoint: str = "main:app"
    error: str | None = None
    started_at: str
    completed_at: str | None = None
    findings_count: int = 0
    high_risk_count: int = 0
    framework: str | None = None
    routes: list[DiscoveredRoute] = Field(default_factory=list)
    sensors: list[SensorResult] = Field(default_factory=list)
    fixes: list[FixAttempt] = Field(default_factory=list)
    report: FinalSecurityReport = Field(default_factory=FinalSecurityReport)
