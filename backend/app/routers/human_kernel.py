"""Human kernel endpoints.

The "human kernel" is the interface through which human owners complete
actions that cannot be automated: SSN/ITIN entry, KYC verification,
payment approval, and document signing.

Each endpoint serves a secure, time-limited form that the agent sends
to the owner via their preferred messaging channel (Signal, Telegram,
WhatsApp, email).
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/human", tags=["human-kernel"])


@router.get(
    "/secure/{token}",
    summary="Render secure action form",
    description=(
        "Returns the secure form for a pending human action (SSN entry, "
        "payment approval, etc.). The token is time-limited and single-use."
    ),
)
async def get_secure_form(token: str) -> dict[str, str]:
    return {"token": token, "status": "not_implemented"}


@router.post(
    "/secure/{token}/submit",
    summary="Submit secure action",
    description=(
        "Submit the completed human action (SSN, payment approval, signature). "
        "On success, fires a webhook to the agent and advances the entity status."
    ),
)
async def submit_secure_action(token: str) -> dict[str, str]:
    return {"token": token, "status": "not_implemented"}


@router.get(
    "/secure/{token}/status",
    summary="Check action status",
    description="Check whether the human owner has completed the required action.",
)
async def check_action_status(token: str) -> dict[str, str]:
    return {"token": token, "status": "not_implemented"}
