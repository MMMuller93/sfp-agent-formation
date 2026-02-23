"""Webhook endpoints.

Handles inbound webhooks (Stripe payment events) and outbound webhook
registration (agents register to receive entity status updates).
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "",
    summary="Register webhook",
    description=(
        "Register a URL to receive entity status update notifications. "
        "The registered endpoint will receive POST requests with status "
        "change payloads as the entity progresses through the formation pipeline."
    ),
    status_code=201,
)
async def register_webhook() -> dict[str, str]:
    return {"status": "not_implemented", "message": "Webhook registration — implementation pending"}


@router.post(
    "/stripe",
    summary="Stripe webhook receiver",
    description="Receives Stripe payment events (payment_intent.succeeded, etc.).",
)
async def stripe_webhook() -> dict[str, str]:
    return {"status": "not_implemented", "message": "Stripe webhook — implementation pending"}
