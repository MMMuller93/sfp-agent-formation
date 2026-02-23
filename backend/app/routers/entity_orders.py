"""Entity order endpoints.

Handles the full lifecycle of entity formation orders: creation,
status queries, name checks, document generation, filing, and
post-formation workflows (EIN, bank pack, activation).
"""

from __future__ import annotations

import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import EntityOrder
from app.schemas.entity_order import (
    CreateOrderRequest,
    OrderListResponse,
    OrderResponse,
    OrderSummary,
    StateTransitionResponse,
)
from app.services import entity_order_service
from app.services.state_machine import OrderState, transition_order

router = APIRouter(prefix="/entity-orders", tags=["entity-orders"])


# ---------------------------------------------------------------------------
# Request bodies for simple updates
# ---------------------------------------------------------------------------


class UpdateNameRequest(BaseModel):
    """Body for PATCH /{order_id} — update the requested entity name."""

    requested_name: str = Field(
        ..., min_length=1, max_length=255, description="New entity name"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_order_or_404(
    session: AsyncSession, order_id: UUID
) -> EntityOrder:
    """Fetch an order by ID or raise 404."""
    order = await entity_order_service.get_order(session, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


async def _do_transition(
    session: AsyncSession,
    order_id: UUID,
    target_state: str,
    *,
    actor: str = "api",
    details: dict | None = None,
) -> StateTransitionResponse:
    """Load an order, attempt a state transition, and return the response."""
    order = await _get_order_or_404(session, order_id)
    previous_state = order.state

    try:
        order = await transition_order(
            session, order, target_state, actor=actor, details=details
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    now = datetime.datetime.now(datetime.timezone.utc)
    return StateTransitionResponse(
        previous_state=previous_state,
        new_state=order.state,
        timestamp=now,
        order=entity_order_service.build_order_response(order),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=OrderResponse,
    status_code=201,
    summary="Create entity formation order",
    description=(
        "Start a new entity formation order. Requires at least one member. "
        "Returns the created order with pricing and next required actions."
    ),
)
async def create_order(
    request: CreateOrderRequest,
    session: AsyncSession = Depends(get_db),
) -> OrderResponse:
    order = await entity_order_service.create_order(session, request)
    return entity_order_service.build_order_response(order)


@router.get(
    "",
    response_model=OrderListResponse,
    summary="List entity orders",
    description="Paginated list of entity orders with optional filtering.",
)
async def list_orders(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    jurisdiction: str | None = Query(None, description="Filter by jurisdiction code"),
    state: str | None = Query(None, description="Filter by order state"),
    session: AsyncSession = Depends(get_db),
) -> OrderListResponse:
    orders, total = await entity_order_service.list_orders(
        session,
        page=page,
        per_page=per_page,
        jurisdiction=jurisdiction,
        state=state,
    )
    return OrderListResponse(
        orders=[
            OrderSummary(
                id=o.id,
                requested_name=o.requested_name,
                state=o.state,
                jurisdiction=o.jurisdiction,
                vehicle_type=o.vehicle_type,
                created_at=o.created_at,
            )
            for o in orders
        ],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get entity order",
    description="Retrieve a single entity order by ID with next required actions.",
)
async def get_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> OrderResponse:
    order = await _get_order_or_404(session, order_id)
    return entity_order_service.build_order_response(order)


@router.patch(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Update entity name",
    description=(
        "Update the requested entity name. Only allowed in draft or "
        "name_check_failed states."
    ),
)
async def update_order(
    order_id: UUID,
    body: UpdateNameRequest,
    session: AsyncSession = Depends(get_db),
) -> OrderResponse:
    order = await _get_order_or_404(session, order_id)
    try:
        order = await entity_order_service.update_order_name(
            session, order, body.requested_name
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return entity_order_service.build_order_response(order)


@router.post(
    "/{order_id}/name-check",
    response_model=StateTransitionResponse,
    summary="Run name availability check",
    description=(
        "Check whether the requested entity name is available in the target "
        "jurisdiction. Transitions intake_complete -> name_check_passed."
    ),
)
async def name_check(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StateTransitionResponse:
    return await _do_transition(
        session,
        order_id,
        OrderState.NAME_CHECK_PASSED,
        actor="api",
        details={"stub": True, "result": "name_available"},
    )


@router.post(
    "/{order_id}/documents/generate",
    response_model=StateTransitionResponse,
    summary="Generate formation documents",
    description=(
        "Generate operating agreement, certificate of formation, and Agent "
        "Authority Schedule. Transitions human_kernel_completed -> docs_generated."
    ),
)
async def generate_documents(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StateTransitionResponse:
    return await _do_transition(
        session,
        order_id,
        OrderState.DOCS_GENERATED,
        actor="api",
        details={"stub": True, "documents": "pending_generation"},
    )


@router.post(
    "/{order_id}/filing",
    response_model=StateTransitionResponse,
    summary="Submit state filing",
    description=(
        "Submit formation documents to the state for filing. "
        "Transitions docs_generated -> state_filing_submitted."
    ),
)
async def submit_filing(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StateTransitionResponse:
    return await _do_transition(
        session,
        order_id,
        OrderState.STATE_FILING_SUBMITTED,
        actor="api",
        details={"stub": True, "channel": "pending"},
    )


@router.post(
    "/{order_id}/ein",
    response_model=StateTransitionResponse,
    summary="Start EIN application",
    description=(
        "Initiate IRS EIN application (Form SS-4) for the formed entity. "
        "Transitions state_confirmed -> ein_pending."
    ),
)
async def apply_ein(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StateTransitionResponse:
    return await _do_transition(
        session,
        order_id,
        OrderState.EIN_PENDING,
        actor="api",
        details={"stub": True, "form": "ss4"},
    )


@router.post(
    "/{order_id}/bank-pack",
    response_model=StateTransitionResponse,
    summary="Generate bank pack",
    description=(
        "Generate the bank-pack document bundle for banking introduction. "
        "Transitions ein_issued -> bank_pack_ready."
    ),
)
async def generate_bank_pack(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StateTransitionResponse:
    return await _do_transition(
        session,
        order_id,
        OrderState.BANK_PACK_READY,
        actor="api",
        details={"stub": True, "bundle": "pending_generation"},
    )


@router.post(
    "/{order_id}/activate",
    response_model=StateTransitionResponse,
    summary="Activate entity",
    description=(
        "Mark the entity as fully formed and active. "
        "Transitions bank_pack_ready -> active."
    ),
)
async def activate_entity(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StateTransitionResponse:
    return await _do_transition(
        session,
        order_id,
        OrderState.ACTIVE,
        actor="api",
        details={"activation": "complete"},
    )
