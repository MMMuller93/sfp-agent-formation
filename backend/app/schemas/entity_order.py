"""Pydantic v2 schemas for entity-order endpoints.

All request/response models live here.  ``OrderResponse`` is the canonical
representation of an entity order, including the dynamically-computed
``next_required_actions`` list that tells the caller exactly what to do
next.
"""

from __future__ import annotations

import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Nested input models
# ---------------------------------------------------------------------------


class MemberInput(BaseModel):
    """A natural person to associate with the entity order."""

    legal_name: str = Field(
        ..., min_length=1, max_length=255, description="Full legal name"
    )
    email: Optional[str] = Field(
        None, max_length=320, description="Contact email"
    )
    role: str = Field(
        "member",
        description="Role in the entity: member | manager | registered_agent | responsible_party",
    )
    ownership_percentage: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="Ownership stake as a percentage (0-100)"
    )

    @field_validator("role")
    @classmethod
    def _validate_role(cls, v: str) -> str:
        allowed = {"member", "manager", "registered_agent", "responsible_party"}
        if v not in allowed:
            raise ValueError(f"role must be one of {sorted(allowed)}, got {v!r}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "legal_name": "Jane Doe",
                    "email": "jane@example.com",
                    "role": "member",
                    "ownership_percentage": 50.0,
                }
            ]
        }
    }


class AgentInput(BaseModel):
    """An AI agent to register as part of the entity structure."""

    display_name: str = Field(
        ..., min_length=1, max_length=255, description="Display name for the agent"
    )
    authority_scope: dict[str, Any] = Field(
        ..., description="JSON object describing what the agent is authorised to do"
    )
    transaction_limit_cents: Optional[int] = Field(
        None, ge=0, description="Per-transaction spending limit in cents"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "display_name": "Treasury Agent v1.2",
                    "authority_scope": {
                        "can_sign_checks": True,
                        "can_initiate_wires": True,
                        "max_single_wire_cents": 50000_00,
                    },
                    "transaction_limit_cents": 100000_00,
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Create request
# ---------------------------------------------------------------------------


class CreateOrderRequest(BaseModel):
    """Payload for ``POST /v1/entity-orders``."""

    jurisdiction: str = Field(
        ..., min_length=2, max_length=10, description="State code, e.g. DE, WY"
    )
    vehicle_type: str = Field(
        ..., description="Entity type: llc | dao_llc | corporation"
    )
    requested_name: str = Field(
        ..., min_length=1, max_length=255, description="Desired entity name"
    )
    service_tier: str = Field(
        "self_serve", description="Service tier: self_serve | managed | autonomous"
    )
    members: list[MemberInput] = Field(
        ..., min_length=1, description="At least one member is required"
    )
    agent: Optional[AgentInput] = Field(
        None, description="Optional AI agent to register"
    )
    metadata: Optional[dict[str, Any]] = Field(
        None, description="Arbitrary metadata to store with the order"
    )

    @field_validator("vehicle_type")
    @classmethod
    def _validate_vehicle_type(cls, v: str) -> str:
        allowed = {"llc", "dao_llc", "corporation"}
        if v not in allowed:
            raise ValueError(f"vehicle_type must be one of {sorted(allowed)}, got {v!r}")
        return v

    @field_validator("service_tier")
    @classmethod
    def _validate_service_tier(cls, v: str) -> str:
        allowed = {"self_serve", "managed", "autonomous"}
        if v not in allowed:
            raise ValueError(f"service_tier must be one of {sorted(allowed)}, got {v!r}")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "jurisdiction": "DE",
                    "vehicle_type": "llc",
                    "requested_name": "Meridian Autonomous Holdings LLC",
                    "service_tier": "managed",
                    "members": [
                        {
                            "legal_name": "Jane Doe",
                            "email": "jane@example.com",
                            "role": "member",
                            "ownership_percentage": 100.0,
                        }
                    ],
                    "agent": {
                        "display_name": "Treasury Agent v1.2",
                        "authority_scope": {
                            "can_sign_checks": True,
                            "can_initiate_wires": True,
                        },
                        "transaction_limit_cents": 100000_00,
                    },
                    "metadata": {"source": "api", "campaign": "launch_q1"},
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ActionItem(BaseModel):
    """Describes a single action the caller should (or must) take next."""

    action: str = Field(..., description="Machine-readable action identifier")
    endpoint: Optional[str] = Field(
        None, description="API endpoint to call, if applicable"
    )
    description: str = Field(..., description="Human-readable guidance")
    required: bool = Field(
        ..., description="Whether this action is mandatory to progress"
    )


class OrderResponse(BaseModel):
    """Canonical representation of an entity order."""

    id: UUID
    jurisdiction: str
    vehicle_type: str
    requested_name: str
    formatted_name: Optional[str] = None
    state: str
    service_tier: str
    pricing_cents: int
    payment_status: str
    next_required_actions: list[ActionItem] = Field(
        default_factory=list,
        description="Actions the caller should take to advance the order",
    )
    created_at: datetime.datetime
    updated_at: Optional[datetime.datetime] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "jurisdiction": "DE",
                    "vehicle_type": "llc",
                    "requested_name": "Meridian Autonomous Holdings LLC",
                    "formatted_name": None,
                    "state": "draft",
                    "service_tier": "managed",
                    "pricing_cents": 79900,
                    "payment_status": "unpaid",
                    "next_required_actions": [
                        {
                            "action": "complete_intake",
                            "endpoint": "POST /v1/entity-orders/a1b2c3d4-e5f6-7890-abcd-ef1234567890/intake",
                            "description": "Submit member/agent details to complete intake",
                            "required": True,
                        }
                    ],
                    "created_at": "2026-02-22T18:00:00Z",
                    "updated_at": None,
                }
            ]
        },
    }


class OrderSummary(BaseModel):
    """Lightweight order representation for list endpoints."""

    id: UUID
    requested_name: str
    state: str
    jurisdiction: str
    vehicle_type: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """Paginated list of orders."""

    orders: list[OrderSummary]
    total: int = Field(..., ge=0, description="Total matching orders")
    page: int = Field(..., ge=1)
    per_page: int = Field(..., ge=1)


class StateTransitionResponse(BaseModel):
    """Response returned after a successful state transition."""

    previous_state: str
    new_state: str
    timestamp: datetime.datetime
    order: OrderResponse
