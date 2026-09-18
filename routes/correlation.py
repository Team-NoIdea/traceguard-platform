"""HTTP boundary for evidence correlation and rescan validation."""

from fastapi import APIRouter, Depends
from services.authentication import current_user

from schemas.correlation import CorrelationRequest, FinalSecurityReport, ValidationResult
from schemas.finding import SecurityFinding
from services import correlation_service

router = APIRouter(prefix="/correlation", tags=["correlation"], dependencies=[Depends(current_user)])


@router.post("/report", response_model=FinalSecurityReport)
def build_report(payload: CorrelationRequest) -> FinalSecurityReport:
    return correlation_service.correlate(payload)


@router.post("/validate", response_model=list[ValidationResult])
def validate_report(original: FinalSecurityReport, rescanned: list[SecurityFinding]) -> list[ValidationResult]:
    return correlation_service.validate_rescan(original, rescanned)