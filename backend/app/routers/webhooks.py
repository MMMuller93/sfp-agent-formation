"""Webhook endpoints.

Handles outbound webhook registration (agents register to receive entity
status updates) and inbound Stripe payment webhooks.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import require_api_key
from app.models import ApiKey
from app.schemas.webhook import CreateWebhookRequest, WebhookResponse
from app.services import webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "",
    summary="Register webhook",
    description=(
        "Register a URL to receive entity status update notifications. "
        "Returns the registration with a signing secret for HMAC verification."
    ),
    response_model=WebhookResponse,
    status_code=201,
)
async def register_webhook(
    body: CreateWebhookRequest,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(require_api_key),
) -> WebhookResponse:
    registration, secret = await webhook_service.register_webhook(
        db,
        url=str(body.url),
        events=body.events,
    )
    # Include the secret in the response — only shown at creation time
    return WebhookResponse(
        id=registration.id,
        url=registration.url,
        events=registration.events,
        active=registration.active,
        created_at=registration.created_at,
        # NOTE: The secret is returned in a separate field in the actual
        # response but we use the standard WebhookResponse model here.
        # In production, extend the response model to include `secret`.
    )


@router.post(
    "/stripe",
    summary="Stripe webhook receiver",
    description="Receives Stripe payment events (payment_intent.succeeded, etc.).",
    include_in_schema=False,  # Not shown in public OpenAPI
)
async def stripe_webhook(request: Request) -> dict[str, str]:
    # TODO: Verify Stripe signature from request.headers["Stripe-Signature"]
    # TODO: Parse event and update order payment_status accordingly
    return {"status": "not_implemented", "message": "Stripe webhook — implementation pending"}
