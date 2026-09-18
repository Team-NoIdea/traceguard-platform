"""HTTP boundary for the feedback-driven LangGraph workflow."""

from fastapi import APIRouter, Depends
from services.authentication import current_user

from schemas.correlation import CorrelationRequest, FinalSecurityReport
from services.langgraph_pipeline import run_workflow

router = APIRouter(prefix="/correlation", tags=["correlation"], dependencies=[Depends(current_user)])


@router.post("/workflow", response_model=FinalSecurityReport)
def run_correlation_workflow(payload: CorrelationRequest) -> FinalSecurityReport:
    return run_workflow(payload)
