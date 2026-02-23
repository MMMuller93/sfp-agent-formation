"""Entity-order state machine.

Defines every legal state, the allowed transitions between them, and
helper functions for advancing an order through its lifecycle.  All
mutations go through ``transition_order`` which validates the move,
updates the order, appends to its JSONB history, and creates an
``AuditEvent`` row — guaranteeing a complete, tamper-evident audit trail.
"""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent, EntityOrder

# ---------------------------------------------------------------------------
# State enum
# ---------------------------------------------------------------------------


class OrderState(StrEnum):
    """Every state an EntityOrder can be in.

    Using StrEnum so the values are plain strings that serialise cleanly
    into JSON, Pydantic models, and JSONB columns.
    """

    DRAFT = "draft"
    INTAKE_COMPLETE = "intake_complete"
    NAME_CHECK_PASSED = "name_check_passed"
    NAME_CHECK_FAILED = "name_check_failed"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_COMPLETE = "payment_complete"
    HUMAN_KERNEL_REQUIRED = "human_kernel_required"
    HUMAN_KERNEL_COMPLETED = "human_kernel_completed"
    KERNEL_EXPIRED = "kernel_expired"
    SANCTIONS_BLOCKED = "sanctions_blocked"
    DOCS_GENERATED = "docs_generated"
    STATE_FILING_SUBMITTED = "state_filing_submitted"
    STATE_CONFIRMED = "state_confirmed"
    FILING_REJECTED = "filing_rejected"
    EIN_PENDING = "ein_pending"
    EIN_MANUAL_REVIEW = "ein_manual_review"
    EIN_ISSUED = "ein_issued"
    BANK_PACK_READY = "bank_pack_ready"
    ACTIVE = "active"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ---------------------------------------------------------------------------
# Transition table
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[str, list[str]] = {
    OrderState.DRAFT: [OrderState.INTAKE_COMPLETE, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.INTAKE_COMPLETE: [
        OrderState.NAME_CHECK_PASSED,
        OrderState.NAME_CHECK_FAILED,
        OrderState.FAILED,
        OrderState.CANCELLED,
    ],
    OrderState.NAME_CHECK_FAILED: [OrderState.INTAKE_COMPLETE, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.NAME_CHECK_PASSED: [OrderState.PAYMENT_PENDING, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.PAYMENT_PENDING: [
        OrderState.PAYMENT_COMPLETE,
        OrderState.PAYMENT_FAILED,
        OrderState.FAILED,
        OrderState.CANCELLED,
    ],
    OrderState.PAYMENT_FAILED: [OrderState.PAYMENT_PENDING, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.PAYMENT_COMPLETE: [OrderState.HUMAN_KERNEL_REQUIRED, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.HUMAN_KERNEL_REQUIRED: [
        OrderState.HUMAN_KERNEL_COMPLETED,
        OrderState.KERNEL_EXPIRED,
        OrderState.SANCTIONS_BLOCKED,
        OrderState.FAILED,
        OrderState.CANCELLED,
    ],
    OrderState.KERNEL_EXPIRED: [OrderState.HUMAN_KERNEL_REQUIRED, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.SANCTIONS_BLOCKED: [OrderState.FAILED],
    OrderState.HUMAN_KERNEL_COMPLETED: [OrderState.DOCS_GENERATED, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.DOCS_GENERATED: [OrderState.STATE_FILING_SUBMITTED, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.STATE_FILING_SUBMITTED: [
        OrderState.STATE_CONFIRMED,
        OrderState.FILING_REJECTED,
        OrderState.FAILED,
        OrderState.CANCELLED,
    ],
    OrderState.FILING_REJECTED: [OrderState.DOCS_GENERATED, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.STATE_CONFIRMED: [OrderState.EIN_PENDING, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.EIN_PENDING: [
        OrderState.EIN_ISSUED,
        OrderState.EIN_MANUAL_REVIEW,
        OrderState.FAILED,
        OrderState.CANCELLED,
    ],
    OrderState.EIN_MANUAL_REVIEW: [OrderState.EIN_ISSUED, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.EIN_ISSUED: [OrderState.BANK_PACK_READY, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.BANK_PACK_READY: [OrderState.ACTIVE, OrderState.FAILED, OrderState.CANCELLED],
    OrderState.ACTIVE: [],       # terminal — fully formed
    OrderState.FAILED: [],       # terminal — unrecoverable
    OrderState.CANCELLED: [],    # terminal — user/ops cancelled
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def can_transition(current_state: str, target_state: str) -> bool:
    """Return True if *target_state* is a legal successor of *current_state*."""
    return target_state in VALID_TRANSITIONS.get(current_state, [])


def is_terminal(state: str) -> bool:
    """Return True if *state* has no outgoing transitions."""
    return VALID_TRANSITIONS.get(state, []) == []


# ---------------------------------------------------------------------------
# Core transition function
# ---------------------------------------------------------------------------


async def transition_order(
    session: AsyncSession,
    order: EntityOrder,
    new_state: str,
    *,
    actor: str = "system",
    details: dict[str, Any] | None = None,
) -> EntityOrder:
    """Advance *order* to *new_state*, recording the change atomically.

    1. Validates that the transition is allowed.
    2. Updates ``order.state``.
    3. Appends a record to ``order.state_history`` (JSONB).
    4. Creates an ``AuditEvent`` row.
    5. If *new_state* is ``active``, stamps ``completed_at``.

    The caller is responsible for committing the session.

    Raises
    ------
    ValueError
        If the transition from the current state to *new_state* is not
        permitted by ``VALID_TRANSITIONS``.
    """
    previous_state = order.state

    if not can_transition(previous_state, new_state):
        allowed = VALID_TRANSITIONS.get(previous_state, [])
        raise ValueError(
            f"Invalid transition: {previous_state!r} -> {new_state!r}. "
            f"Allowed targets from {previous_state!r}: {allowed}"
        )

    now = datetime.datetime.now(datetime.timezone.utc)

    # --- mutate order ---
    order.state = new_state

    # Append to JSONB history.  We copy the list so SQLAlchemy detects the
    # mutation on the JSONB column (it tracks identity, not deep equality).
    history_entry: dict[str, Any] = {
        "state": new_state,
        "previous_state": previous_state,
        "timestamp": now.isoformat(),
        "actor": actor,
    }
    if details:
        history_entry["details"] = details

    order.state_history = [*order.state_history, history_entry]

    if new_state == OrderState.ACTIVE:
        order.completed_at = now

    # --- audit event ---
    audit = AuditEvent(
        order_id=order.id,
        actor=actor,
        action=f"state_transition:{previous_state}->{new_state}",
        details={
            "previous_state": previous_state,
            "new_state": new_state,
            **(details or {}),
        },
    )
    session.add(audit)

    return order


# ---------------------------------------------------------------------------
# Next-action guidance
# ---------------------------------------------------------------------------

# Maps each non-terminal state to the action(s) the caller should take next.
_NEXT_ACTIONS: dict[str, list[dict[str, Any]]] = {
    OrderState.DRAFT: [
        {
            "action": "complete_intake",
            "endpoint": "POST /v1/entity-orders/{id}/intake",
            "description": "Submit member/agent details to complete intake",
            "required": True,
        },
    ],
    OrderState.INTAKE_COMPLETE: [
        {
            "action": "name_check",
            "endpoint": "POST /v1/entity-orders/{id}/name-check",
            "description": "Check entity name availability with the state",
            "required": True,
        },
    ],
    OrderState.NAME_CHECK_FAILED: [
        {
            "action": "update_name",
            "endpoint": "PATCH /v1/entity-orders/{id}",
            "description": "Update requested_name and re-submit intake",
            "required": True,
        },
    ],
    OrderState.NAME_CHECK_PASSED: [
        {
            "action": "create_payment",
            "endpoint": "POST /v1/entity-orders/{id}/payment",
            "description": "Create a payment intent to begin checkout",
            "required": True,
        },
    ],
    OrderState.PAYMENT_PENDING: [
        {
            "action": "confirm_payment",
            "endpoint": "POST /v1/entity-orders/{id}/payment/confirm",
            "description": "Confirm the Stripe payment intent",
            "required": True,
        },
    ],
    OrderState.PAYMENT_FAILED: [
        {
            "action": "retry_payment",
            "endpoint": "POST /v1/entity-orders/{id}/payment",
            "description": "Create a new payment intent after failure",
            "required": True,
        },
    ],
    OrderState.PAYMENT_COMPLETE: [
        {
            "action": "start_human_kernel",
            "endpoint": "POST /v1/entity-orders/{id}/human-kernel",
            "description": "Initiate the Human Kernel identity-verification session",
            "required": True,
        },
    ],
    OrderState.HUMAN_KERNEL_REQUIRED: [
        {
            "action": "complete_human_kernel",
            "endpoint": "POST /v1/human-kernel/{token}/complete",
            "description": "Complete identity verification, KYC, and OFAC screening",
            "required": True,
        },
    ],
    OrderState.KERNEL_EXPIRED: [
        {
            "action": "restart_human_kernel",
            "endpoint": "POST /v1/entity-orders/{id}/human-kernel",
            "description": "Re-initiate an expired Human Kernel session",
            "required": True,
        },
    ],
    OrderState.SANCTIONS_BLOCKED: [
        {
            "action": "manual_review",
            "endpoint": None,
            "description": "Order blocked by OFAC/sanctions screening — requires manual ops review",
            "required": False,
        },
    ],
    OrderState.HUMAN_KERNEL_COMPLETED: [
        {
            "action": "generate_documents",
            "endpoint": "POST /v1/entity-orders/{id}/documents/generate",
            "description": "Generate formation documents from templates",
            "required": True,
        },
    ],
    OrderState.DOCS_GENERATED: [
        {
            "action": "submit_filing",
            "endpoint": "POST /v1/entity-orders/{id}/filing",
            "description": "Submit formation filing to the state",
            "required": True,
        },
    ],
    OrderState.STATE_FILING_SUBMITTED: [
        {
            "action": "await_state_confirmation",
            "endpoint": None,
            "description": "Waiting for state confirmation — no action required",
            "required": False,
        },
    ],
    OrderState.FILING_REJECTED: [
        {
            "action": "regenerate_documents",
            "endpoint": "POST /v1/entity-orders/{id}/documents/generate",
            "description": "Fix issues and regenerate formation documents",
            "required": True,
        },
    ],
    OrderState.STATE_CONFIRMED: [
        {
            "action": "apply_for_ein",
            "endpoint": "POST /v1/entity-orders/{id}/ein",
            "description": "Submit IRS Form SS-4 for an EIN",
            "required": True,
        },
    ],
    OrderState.EIN_PENDING: [
        {
            "action": "await_ein",
            "endpoint": None,
            "description": "Waiting for EIN issuance — no action required",
            "required": False,
        },
    ],
    OrderState.EIN_MANUAL_REVIEW: [
        {
            "action": "resolve_ein_review",
            "endpoint": "POST /v1/entity-orders/{id}/ein/resolve",
            "description": "Resolve EIN manual review (ops intervention required)",
            "required": True,
        },
    ],
    OrderState.EIN_ISSUED: [
        {
            "action": "generate_bank_pack",
            "endpoint": "POST /v1/entity-orders/{id}/bank-pack",
            "description": "Generate the bank-pack document bundle",
            "required": True,
        },
    ],
    OrderState.BANK_PACK_READY: [
        {
            "action": "activate",
            "endpoint": "POST /v1/entity-orders/{id}/activate",
            "description": "Mark the entity as fully active",
            "required": True,
        },
    ],
}


def get_next_required_actions(order: EntityOrder) -> list[dict[str, Any]]:
    """Return action descriptors for the next step(s) given *order*'s current state.

    Each descriptor contains:
    - ``action``      – machine-readable action name
    - ``endpoint``    – the API endpoint to call (or None if no API action)
    - ``description`` – human-readable guidance
    - ``required``    – whether the action is mandatory to progress

    Terminal states (``active``, ``failed``) return an empty list.
    """
    actions = _NEXT_ACTIONS.get(order.state, [])

    # Interpolate the order ID into endpoint templates
    resolved: list[dict[str, Any]] = []
    for action in actions:
        entry = {**action}
        if entry.get("endpoint") and "{id}" in entry["endpoint"]:
            entry["endpoint"] = entry["endpoint"].replace("{id}", str(order.id))
        resolved.append(entry)

    return resolved
