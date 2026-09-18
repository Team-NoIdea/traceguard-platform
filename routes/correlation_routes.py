"""
Evidence correlation routes (Phase 3).

Routes stay thin: they validate the request via CorrelationRequest,
delegate to services.correlation_service, and shape the response with
CorrelationResponse. No scoring/merge logic lives here.
"""

from fastapi import APIRouter, Depends
from services.authentication import current_user

from schemas.correlation import (
    CorrelationEntry,
    CorrelationRequest,
    CorrelationResponse,
)
from services import correlation_service

router = APIRouter(prefix="/correlate", tags=["correlation"], dependencies=[Depends(current_user)])


@router.post("", response_model=CorrelationResponse)
def correlate_findings(payload: CorrelationRequest) -> CorrelationResponse:
    """Correlate static findings against runtime evidence and merge matches."""
    findings, entries = correlation_service.correlate_static_runtime(
        payload.static_findings, payload.runtime_evidence, payload.threshold
    )
    return CorrelationResponse(
        findings=findings,
        correlations=[CorrelationEntry(**entry) for entry in entries],
    )


@router.get("/mock-data", response_model=CorrelationResponse)
def correlate_mock_data() -> CorrelationResponse:
    """Convenience endpoint: run correlation over the bundled
    mock-data/static.json + mock-data/runtime.json fixtures, at the
    default threshold â€” useful for demos and manual sanity checks."""
    static_findings = correlation_service.load_mock_static_findings()
    runtime_evidence = correlation_service.load_mock_runtime_evidence()
    findings, entries = correlation_service.correlate_static_runtime(
        static_findings, runtime_evidence
    )
    return CorrelationResponse(
        findings=findings,
        correlations=[CorrelationEntry(**entry) for entry in entries],
    )
