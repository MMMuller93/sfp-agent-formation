"""Health check endpoint.

Mounted at the application root (no /v1 prefix) so that load balancers
and orchestration systems can probe without authentication.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns service status and version. Used by load balancers and monitoring.",
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="1.0.0")
