"""Human kernel endpoints.

The "human kernel" is the interface through which human owners complete
actions that cannot be automated: SSN/ITIN entry, KYC verification,
payment approval, and document signing.

Two route groups:
1. Agent-facing: POST /v1/entity-orders/{id}/human-kernel (in entity_orders router)
2. Human-facing: GET/POST /v1/human/secure/{token} (this router, token-auth, no API key)
"""

from __future__ import annotations

import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import human_kernel_service

router = APIRouter(prefix="/human", tags=["human-kernel"])


# ---------------------------------------------------------------------------
# Response schemas (local to this router)
# ---------------------------------------------------------------------------


class KernelSessionStatus(BaseModel):
    """Status of a human kernel session."""
    token_prefix: str = Field(..., description="First 8 chars of token")
    status: str = Field(..., description="pending | in_progress | completed | expired")
    completed_steps: list[str]
    remaining_steps: list[str]
    expires_at: datetime.datetime
    is_expired: bool


class StepSubmission(BaseModel):
    """Payload for completing a kernel step."""
    step: str = Field(
        ...,
        description="Step to complete: pii_collection | kyc_verification | document_signing | attestation",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Step-specific data (e.g., encrypted SSN for pii_collection)",
    )


class StepResponse(BaseModel):
    """Response after completing a kernel step."""
    step: str
    status: str
    completed_steps: list[str]
    remaining_steps: list[str]
    all_complete: bool


# ---------------------------------------------------------------------------
# Routes — these use TOKEN auth, NOT API key auth.
# The human accesses these via a secure link sent by the agent.
# ---------------------------------------------------------------------------


@router.get(
    "/secure/{token}",
    summary="Get kernel session status",
    description=(
        "Returns the current status of a human kernel session. "
        "Used by the secure form to show which steps are pending."
    ),
    response_model=KernelSessionStatus,
)
async def get_session_status(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> KernelSessionStatus:
    kernel_session = await human_kernel_service.get_session_by_token(db, token)

    if kernel_session is None:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    now = datetime.datetime.now(datetime.timezone.utc)
    is_expired = kernel_session.expires_at < now and kernel_session.status != "completed"
    remaining = [
        s for s in human_kernel_service.KERNEL_STEPS
        if s not in kernel_session.completed_steps
    ]

    return KernelSessionStatus(
        token_prefix=token[:8],
        status=kernel_session.status,
        completed_steps=kernel_session.completed_steps,
        remaining_steps=remaining,
        expires_at=kernel_session.expires_at,
        is_expired=is_expired,
    )


@router.post(
    "/secure/{token}/submit",
    summary="Submit a kernel step",
    description=(
        "Complete a step in the human kernel flow. "
        "On success, advances the session. When all steps complete, "
        "the order transitions to human_kernel_completed and a webhook fires."
    ),
    response_model=StepResponse,
)
async def submit_step(
    token: str,
    body: StepSubmission,
    db: AsyncSession = Depends(get_db),
) -> StepResponse:
    kernel_session = await human_kernel_service.get_session_by_token(db, token)

    if kernel_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if kernel_session.status == "expired":
        raise HTTPException(status_code=410, detail="Session has expired")

    try:
        kernel_session = await human_kernel_service.complete_step(
            db, kernel_session, body.step,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    remaining = [
        s for s in human_kernel_service.KERNEL_STEPS
        if s not in kernel_session.completed_steps
    ]
    all_complete = len(remaining) == 0

    return StepResponse(
        step=body.step,
        status=kernel_session.status,
        completed_steps=kernel_session.completed_steps,
        remaining_steps=remaining,
        all_complete=all_complete,
    )


@router.get(
    "/secure/{token}/status",
    summary="Check session completion",
    description="Quick check whether the human owner has completed all required steps.",
)
async def check_completion(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    kernel_session = await human_kernel_service.get_session_by_token(db, token)

    if kernel_session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "token_prefix": token[:8],
        "completed": kernel_session.status == "completed",
        "status": kernel_session.status,
        "steps_done": len(kernel_session.completed_steps),
        "steps_total": len(human_kernel_service.KERNEL_STEPS),
    }
