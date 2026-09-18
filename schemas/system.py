"""
Pydantic response models for system-level endpoints (root + health).

Keeping these separate from route logic means the response "shape" is
defined in exactly one place and can be reused/tested independently of
FastAPI routing.
"""

from pydantic import BaseModel


class ServiceInfoResponse(BaseModel):
    """Response for GET / — basic service identification."""

    service: str
    status: str
    version: str


class HealthResponse(BaseModel):
    """Response for GET /health — liveness check."""

    status: str
