"""Pydantic v2 schemas for webhook endpoints."""

from __future__ import annotations

import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class CreateWebhookRequest(BaseModel):
    """Payload for ``POST /v1/webhooks``."""

    url: HttpUrl = Field(..., description="HTTPS URL to receive webhook POST requests")
    events: list[str] = Field(
        ...,
        min_length=1,
        description=(
            "Event types to subscribe to, e.g. "
            '["order.state_changed", "order.completed", "filing.confirmed"]'
        ),
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://example.com/webhooks/sfp",
                    "events": ["order.state_changed", "order.completed"],
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------


class WebhookResponse(BaseModel):
    """Representation of a webhook registration."""

    id: UUID
    url: str
    events: list[str]
    active: bool
    created_at: datetime.datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
                    "url": "https://example.com/webhooks/sfp",
                    "events": ["order.state_changed", "order.completed"],
                    "active": True,
                    "created_at": "2026-02-22T18:00:00Z",
                }
            ]
        },
    }


class WebhookEventResponse(BaseModel):
    """Representation of a single webhook delivery event."""

    id: UUID
    event_type: str
    status: str = Field(
        ..., description="pending | delivered | failed | dead_letter"
    )
    attempts: int
    last_attempt_at: Optional[datetime.datetime] = None
    next_retry_at: Optional[datetime.datetime] = None
    created_at: datetime.datetime

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "c3d479f4-7ac1-0b58-cc43-72a5670e02b2",
                    "event_type": "order.state_changed",
                    "status": "delivered",
                    "attempts": 1,
                    "last_attempt_at": "2026-02-22T18:01:00Z",
                    "next_retry_at": None,
                    "created_at": "2026-02-22T18:00:30Z",
                }
            ]
        },
    }
