"""Outbound webhook delivery service.

When entity orders change state, registered webhooks are notified.
Delivery uses exponential backoff with a dead-letter queue for
persistent failures.

RETRY SCHEDULE: 1s, 5s, 30s, 5min, 30min (5 attempts max).
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WebhookEvent, WebhookRegistration

logger = logging.getLogger("sfp.webhooks")

# Retry delays in seconds: 1s, 5s, 30s, 5min, 30min
RETRY_DELAYS = [1, 5, 30, 300, 1800]
MAX_ATTEMPTS = len(RETRY_DELAYS)


def sign_payload(payload: dict[str, Any], secret: str) -> str:
    """Create HMAC-SHA256 signature of the payload.
    
    The signature is computed over the canonical JSON representation
    (sorted keys, no whitespace). Consumers verify by computing the
    same HMAC with their secret.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(
        secret.encode(),
        canonical.encode(),
        hashlib.sha256,
    ).hexdigest()


async def enqueue_webhook_event(
    session: AsyncSession,
    *,
    event_type: str,
    payload: dict[str, Any],
) -> list[WebhookEvent]:
    """Enqueue a webhook event for all active registrations that subscribe to this event type.
    
    Creates one WebhookEvent per matching registration.
    Returns the list of created events.
    """
    # Find all active registrations
    result = await session.execute(
        select(WebhookRegistration).where(
            WebhookRegistration.active == True,  # noqa: E712
        )
    )
    registrations = list(result.scalars().all())
    
    events: list[WebhookEvent] = []
    now = datetime.datetime.now(datetime.timezone.utc)
    
    for reg in registrations:
        # Check if registration subscribes to this event type
        # "*" means subscribe to everything
        if "*" not in reg.events and event_type not in reg.events:
            continue
        
        event = WebhookEvent(
            registration_id=reg.id,
            event_type=event_type,
            payload=payload,
            idempotency_key=str(uuid.uuid4()),
            attempts=0,
            status="pending",
            next_retry_at=now,  # deliver immediately
        )
        session.add(event)
        events.append(event)
    
    if events:
        logger.info(
            "Enqueued %d webhook events for event_type=%s",
            len(events), event_type,
        )
    
    return events


async def get_pending_events(
    session: AsyncSession,
    *,
    limit: int = 50,
) -> list[WebhookEvent]:
    """Get pending webhook events that are ready for delivery."""
    now = datetime.datetime.now(datetime.timezone.utc)
    
    result = await session.execute(
        select(WebhookEvent)
        .where(
            WebhookEvent.status.in_(["pending", "retrying"]),
            WebhookEvent.next_retry_at <= now,
        )
        .order_by(WebhookEvent.next_retry_at.asc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def mark_delivered(
    session: AsyncSession,
    event: WebhookEvent,
) -> None:
    """Mark a webhook event as successfully delivered."""
    event.status = "delivered"
    event.attempts += 1
    event.last_attempt_at = datetime.datetime.now(datetime.timezone.utc)
    event.next_retry_at = None


async def mark_failed(
    session: AsyncSession,
    event: WebhookEvent,
) -> None:
    """Mark a webhook delivery attempt as failed and schedule retry.
    
    After MAX_ATTEMPTS, moves to dead_letter status.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    event.attempts += 1
    event.last_attempt_at = now
    
    if event.attempts >= MAX_ATTEMPTS:
        event.status = "dead_letter"
        event.next_retry_at = None
        logger.warning(
            "Webhook event %s moved to dead letter after %d attempts",
            event.id, event.attempts,
        )
    else:
        event.status = "retrying"
        delay = RETRY_DELAYS[event.attempts - 1] if event.attempts - 1 < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
        event.next_retry_at = now + datetime.timedelta(seconds=delay)
        logger.info(
            "Webhook event %s retry %d scheduled for %s",
            event.id, event.attempts, event.next_retry_at,
        )


async def register_webhook(
    session: AsyncSession,
    *,
    url: str,
    events: list[str],
) -> tuple[WebhookRegistration, str]:
    """Register a new webhook endpoint. Returns (registration, secret).
    
    The secret is generated server-side and returned to the caller
    for HMAC signature verification.
    """
    import secrets as stdlib_secrets
    
    secret = stdlib_secrets.token_urlsafe(32)
    
    registration = WebhookRegistration(
        url=url,
        secret=secret,
        events=events,
        active=True,
    )
    session.add(registration)
    await session.flush()
    
    return registration, secret
