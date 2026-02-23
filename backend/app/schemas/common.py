"""Common schemas shared across the API.

Includes generic error responses, health checks, and pagination helpers.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all error handlers."""

    detail: str = Field(..., description="Human-readable error message")
    error_code: Optional[str] = Field(
        None,
        description="Machine-readable error code for programmatic handling",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "detail": "Entity order not found",
                    "error_code": "ORDER_NOT_FOUND",
                },
                {
                    "detail": "Invalid state transition: draft -> active",
                    "error_code": "INVALID_TRANSITION",
                },
            ]
        }
    }


class HealthResponse(BaseModel):
    """Response for the ``GET /health`` endpoint."""

    status: str = Field(..., description="Service status", examples=["ok"])
    version: str = Field(..., description="API version string", examples=["1.0.0"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"status": "ok", "version": "1.0.0"},
            ]
        }
    }


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints.

    Use as a dependency in FastAPI route functions::

        @router.get("/orders")
        async def list_orders(pagination: PaginationParams = Depends()):
            ...
    """

    page: int = Field(1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(
        20,
        ge=1,
        le=100,
        description="Number of results per page (max 100)",
    )

    @property
    def offset(self) -> int:
        """SQL OFFSET derived from page and per_page."""
        return (self.page - 1) * self.per_page
