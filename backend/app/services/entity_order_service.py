"""Core CRUD service layer for entity orders.

All database interactions for entity orders are funnelled through this
module.  Router handlers stay thin — they validate input, call a service
function, and serialise the response.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentRecord, AuditEvent, EntityOrder, NaturalPerson
from app.schemas.entity_order import (
    ActionItem,
    CreateOrderRequest,
    OrderResponse,
)
from app.services.state_machine import OrderState, get_next_required_actions

# ---------------------------------------------------------------------------
# Pricing lookup
# ---------------------------------------------------------------------------

PRICING: dict[tuple[str, str], int] = {
    ("DE", "llc"): 49900,
    ("DE", "corporation"): 59900,
    ("WY", "llc"): 49900,
    ("WY", "dao_llc"): 69900,
}


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def create_order(
    session: AsyncSession, request: CreateOrderRequest
) -> EntityOrder:
    """Create a new entity order with associated persons and agent."""
    pricing_cents = PRICING.get(
        (request.jurisdiction.upper(), request.vehicle_type), 49900
    )

    order = EntityOrder(
        jurisdiction=request.jurisdiction.upper(),
        vehicle_type=request.vehicle_type,
        requested_name=request.requested_name,
        service_tier=request.service_tier,
        pricing_cents=pricing_cents,
        payment_status="unpaid",
        state="draft",
        state_history=[],
        metadata_=request.metadata,
    )
    session.add(order)
    await session.flush()  # get the server-generated UUID

    # Create NaturalPerson records for each member
    for member in request.members:
        person = NaturalPerson(
            order_id=order.id,
            role=member.role,
            legal_name=member.legal_name,
            email=member.email,
            ownership_percentage=member.ownership_percentage,
        )
        session.add(person)

    # Create AgentRecord if provided
    if request.agent:
        agent = AgentRecord(
            order_id=order.id,
            display_name=request.agent.display_name,
            authority_scope=request.agent.authority_scope,
            transaction_limit_cents=request.agent.transaction_limit_cents,
        )
        session.add(agent)

    # Create initial audit event
    audit = AuditEvent(
        order_id=order.id,
        actor="system",
        action="order_created",
        details={
            "jurisdiction": order.jurisdiction,
            "vehicle_type": order.vehicle_type,
            "requested_name": order.requested_name,
        },
    )
    session.add(audit)

    await session.flush()
    return order


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


async def get_order(
    session: AsyncSession, order_id: UUID
) -> EntityOrder | None:
    """Get a single order by ID with all relationships loaded."""
    result = await session.execute(
        select(EntityOrder).where(EntityOrder.id == order_id)
    )
    return result.scalar_one_or_none()


async def list_orders(
    session: AsyncSession,
    *,
    page: int = 1,
    per_page: int = 20,
    jurisdiction: str | None = None,
    state: str | None = None,
) -> tuple[list[EntityOrder], int]:
    """List orders with optional filtering and pagination."""
    query = select(EntityOrder)
    count_query = select(func.count()).select_from(EntityOrder)

    if jurisdiction:
        query = query.where(
            EntityOrder.jurisdiction == jurisdiction.upper()
        )
        count_query = count_query.where(
            EntityOrder.jurisdiction == jurisdiction.upper()
        )
    if state:
        query = query.where(EntityOrder.state == state)
        count_query = count_query.where(EntityOrder.state == state)

    total = (await session.execute(count_query)).scalar_one()

    query = query.order_by(EntityOrder.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await session.execute(query)
    orders = list(result.scalars().all())

    return orders, total


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


async def update_order_name(
    session: AsyncSession, order: EntityOrder, new_name: str
) -> EntityOrder:
    """Update the requested name on an order (only allowed in certain states)."""
    allowed_states = {OrderState.DRAFT, OrderState.NAME_CHECK_FAILED}
    if order.state not in allowed_states:
        raise ValueError(f"Cannot update name in state {order.state!r}")

    order.requested_name = new_name
    order.formatted_name = None  # reset formatted name

    audit = AuditEvent(
        order_id=order.id,
        actor="api",
        action="name_updated",
        details={"new_name": new_name},
    )
    session.add(audit)

    return order


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------


def build_order_response(order: EntityOrder) -> OrderResponse:
    """Convert an ORM EntityOrder to the API response schema."""
    actions = get_next_required_actions(order)
    action_items = [ActionItem(**a) for a in actions]

    return OrderResponse(
        id=order.id,
        jurisdiction=order.jurisdiction,
        vehicle_type=order.vehicle_type,
        requested_name=order.requested_name,
        formatted_name=order.formatted_name,
        state=order.state,
        service_tier=order.service_tier,
        pricing_cents=order.pricing_cents,
        payment_status=order.payment_status,
        next_required_actions=action_items,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
