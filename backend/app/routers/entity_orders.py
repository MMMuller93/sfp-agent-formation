"""Entity order endpoints.

Handles the full lifecycle of entity formation orders: creation,
status queries, name checks, document generation, filing, and
post-formation workflows (EIN, bank pack, activation).
"""

from __future__ import annotations

import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AuditEvent, EntityOrder
from app.schemas.entity_order import (
    CreateOrderRequest,
    OrderListResponse,
    OrderResponse,
    OrderSummary,
    StateTransitionResponse,
)
from app.services import entity_order_service, human_kernel_service
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


class CreateKernelResponse(BaseModel):
    """Response after creating a human kernel session."""

    kernel_url: str = Field(..., description="Secure URL for the human owner")
    token_prefix: str = Field(..., description="First 8 chars of the session token")
    expires_at: datetime.datetime
    suggested_message: str = Field(
        ..., description="Message the agent can relay to the human owner"
    )


class NameCheckResponse(BaseModel):
    """Response from name availability check."""

    available: bool
    jurisdiction: str
    entity_name: str
    message: str
    method: str
    suggestions: list[str] = Field(default_factory=list)
    transition: StateTransitionResponse | None = None


class DocumentSummary(BaseModel):
    """Lightweight document info for list endpoints."""

    id: UUID
    doc_type: str
    template_version: str
    file_hash: str
    signing_status: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class AuditEventResponse(BaseModel):
    """An audit event for the trail endpoint."""

    id: UUID
    actor: str
    action: str
    details: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


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


# ---------------------------------------------------------------------------
# Intake
# ---------------------------------------------------------------------------


@router.post(
    "/{order_id}/intake",
    response_model=StateTransitionResponse,
    summary="Complete intake",
    description=(
        "Mark intake as complete. Transitions draft -> intake_complete. "
        "Call this after the order has been created and all member/agent "
        "details are finalized."
    ),
)
async def complete_intake(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StateTransitionResponse:
    return await _do_transition(
        session,
        order_id,
        OrderState.INTAKE_COMPLETE,
        actor="api",
        details={"method": "api_call"},
    )


# ---------------------------------------------------------------------------
# Name check — wired to name_check_service
# ---------------------------------------------------------------------------


@router.post(
    "/{order_id}/name-check",
    response_model=NameCheckResponse,
    summary="Run name availability check",
    description=(
        "Check whether the requested entity name is available in the target "
        "jurisdiction. If available, transitions to name_check_passed. "
        "If not, transitions to name_check_failed with suggestions."
    ),
)
async def name_check(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> NameCheckResponse:
    from app.services import name_check_service

    order = await _get_order_or_404(session, order_id)
    previous_state = order.state

    # Run the name check
    try:
        result = await name_check_service.check_name_availability(
            jurisdiction=order.jurisdiction,
            entity_name=order.requested_name,
            entity_type=order.vehicle_type,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Name check service unavailable: {exc}",
        ) from exc

    # Transition based on result
    target_state = (
        OrderState.NAME_CHECK_PASSED
        if result["available"]
        else OrderState.NAME_CHECK_FAILED
    )

    try:
        order = await transition_order(
            session,
            order,
            target_state,
            actor="api",
            details={
                "name_check_result": result["available"],
                "method": result["method"],
                "message": result["message"],
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    now = datetime.datetime.now(datetime.timezone.utc)
    transition = StateTransitionResponse(
        previous_state=previous_state,
        new_state=order.state,
        timestamp=now,
        order=entity_order_service.build_order_response(order),
    )

    return NameCheckResponse(
        available=result["available"],
        jurisdiction=result["jurisdiction"],
        entity_name=result["entity_name"],
        message=result["message"],
        method=result["method"],
        suggestions=result.get("suggestions", []),
        transition=transition,
    )


# ---------------------------------------------------------------------------
# Payment (stub — Stripe integration pending)
# ---------------------------------------------------------------------------


@router.post(
    "/{order_id}/payment",
    response_model=StateTransitionResponse,
    summary="Record payment",
    description=(
        "Record a successful payment. Transitions name_check_passed -> "
        "payment_pending, or payment_pending -> payment_complete. "
        "In production, this is triggered by the Stripe webhook."
    ),
)
async def record_payment(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StateTransitionResponse:
    order = await _get_order_or_404(session, order_id)
    previous_state = order.state

    # Determine target state based on current state
    if order.state in (OrderState.NAME_CHECK_PASSED, OrderState.PAYMENT_FAILED):
        target = OrderState.PAYMENT_PENDING
    elif order.state == OrderState.PAYMENT_PENDING:
        target = OrderState.PAYMENT_COMPLETE
    else:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot record payment from state '{order.state}'",
        )

    try:
        order = await transition_order(
            session, order, target, actor="api",
            details={"stub": True, "note": "Stripe integration pending"},
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
# Human kernel — create session for human owner
# ---------------------------------------------------------------------------


@router.post(
    "/{order_id}/human-kernel",
    response_model=CreateKernelResponse,
    summary="Create human kernel session",
    description=(
        "Create a secure session for the human owner to complete required steps "
        "(PII collection, KYC, document signing, attestation). Returns a URL "
        "the agent should relay to the human. Transitions order to "
        "human_kernel_required."
    ),
)
async def create_kernel_session(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> CreateKernelResponse:
    order = await _get_order_or_404(session, order_id)

    try:
        kernel_session = await human_kernel_service.create_kernel_session(
            session, order, actor="api",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    from app.config import get_settings
    settings = get_settings()

    kernel_url = f"{settings.BASE_URL}/kernel/{kernel_session.token}"

    return CreateKernelResponse(
        kernel_url=kernel_url,
        token_prefix=kernel_session.token[:8],
        expires_at=kernel_session.expires_at,
        suggested_message=(
            f"Please complete the required verification steps for your entity "
            f"formation at: {kernel_url}\n\n"
            f"This link expires in 24 hours. You'll need your SSN/ITIN, "
            f"a photo ID for identity verification, and approximately "
            f"5 minutes to complete the process."
        ),
    )


# ---------------------------------------------------------------------------
# Document generation — wired to document_generation_service
# ---------------------------------------------------------------------------


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
    from app.services.document_generation_service import generate_formation_documents

    order = await _get_order_or_404(session, order_id)
    previous_state = order.state

    try:
        documents = await generate_formation_documents(session, order, actor="api")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    # Check if all documents are placeholders/failed (no real rendering)
    real_docs = [d for d in documents if d.template_version not in ("no_template", "render_failed")]
    if len(documents) > 0 and len(real_docs) == 0:
        raise HTTPException(
            status_code=500,
            detail="All document rendering failed — no real documents were generated.",
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    return StateTransitionResponse(
        previous_state=previous_state,
        new_state=order.state,
        timestamp=now,
        order=entity_order_service.build_order_response(order),
    )


@router.get(
    "/{order_id}/documents",
    response_model=list[DocumentSummary],
    summary="List order documents",
    description="List all documents generated for an order.",
)
async def list_documents(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[DocumentSummary]:
    order = await _get_order_or_404(session, order_id)
    return [
        DocumentSummary(
            id=doc.id,
            doc_type=doc.doc_type,
            template_version=doc.template_version,
            file_hash=doc.file_hash,
            signing_status=doc.signing_status,
            created_at=doc.created_at,
        )
        for doc in order.documents
    ]


# ---------------------------------------------------------------------------
# Filing & post-formation
# ---------------------------------------------------------------------------


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
        actor="ops",
        details={"channel": "manual"},
    )


@router.post(
    "/{order_id}/filing/confirm",
    response_model=StateTransitionResponse,
    summary="Confirm state filing",
    description=(
        "Confirm that the state has approved the filing. "
        "Transitions state_filing_submitted -> state_confirmed."
    ),
)
async def confirm_filing(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StateTransitionResponse:
    return await _do_transition(
        session,
        order_id,
        OrderState.STATE_CONFIRMED,
        actor="ops",
        details={"channel": "manual"},
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
        actor="ops",
        details={"form": "ss4"},
    )


@router.post(
    "/{order_id}/ein/issue",
    response_model=StateTransitionResponse,
    summary="Record EIN issuance",
    description=(
        "Record that the IRS has issued the EIN. "
        "Transitions ein_pending -> ein_issued."
    ),
)
async def issue_ein(
    order_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> StateTransitionResponse:
    return await _do_transition(
        session,
        order_id,
        OrderState.EIN_ISSUED,
        actor="ops",
        details={"source": "irs_confirmation"},
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
        details={"bundle": "generated"},
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
        actor="ops",
        details={"activation": "complete"},
    )


# ---------------------------------------------------------------------------
# Audit trail
# ---------------------------------------------------------------------------


@router.get(
    "/{order_id}/audit",
    response_model=list[AuditEventResponse],
    summary="Get audit trail",
    description="Get the audit trail for a specific order, newest first.",
)
async def get_audit_trail(
    order_id: UUID,
    limit: int = Query(100, ge=1, le=500, description="Max events to return"),
    session: AsyncSession = Depends(get_db),
) -> list[AuditEventResponse]:
    from app.services import audit_service

    # Verify order exists
    await _get_order_or_404(session, order_id)

    events = await audit_service.get_audit_trail(session, order_id, limit=limit)
    return [
        AuditEventResponse(
            id=e.id,
            actor=e.actor,
            action=e.action,
            details=e.details,
            ip_address=e.ip_address,
            created_at=e.created_at,
        )
        for e in events
    ]
