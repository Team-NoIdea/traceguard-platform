"""
System-level routes: service identity (/) and liveness (/health).

Routes stay thin on purpose — they only translate HTTP <-> service
calls and shape the response with the Pydantic schema. Any real logic
belongs in services/.
"""

from fastapi import APIRouter

from schemas.system import HealthResponse, ServiceInfoResponse
from services import system_service

router = APIRouter(tags=["system"])


@router.get("/", response_model=ServiceInfoResponse)
def read_root() -> ServiceInfoResponse:
    """Basic service identification — name + status."""
    return ServiceInfoResponse(**system_service.get_service_info())


@router.get("/health", response_model=HealthResponse)
def read_health() -> HealthResponse:
    """Liveness check used by uptime checks / load balancers."""
    return HealthResponse(**system_service.get_health_status())
