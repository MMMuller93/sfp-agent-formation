"""Human kernel session management.

The human kernel is the interface through which human owners perform
actions that cannot be automated: SSN entry, KYC verification,
payment approval, and document signing.

Each session has a cryptographic token, a 24-hour expiry, and tracks
which steps have been completed.
"""

from __future__ import annotations

import datetime
import secrets
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent, EntityOrder, HumanKernelSession
from app.services.state_machine import OrderState, transition_order

# Token length: 48 URL-safe bytes = 64 characters
TOKEN_BYTES = 48
# Session expires after 24 hours
SESSION_TTL_HOURS = 24

# Steps in the human kernel flow
KERNEL_STEPS = ["pii_collection", "kyc_verification", "document_signing", "attestation"]


async def create_kernel_session(
    session: AsyncSession,
    order: EntityOrder,
    *,
    actor: str = "system",
) -> HumanKernelSession:
    """Create a new human kernel session for an order.
    
    The order must be in 'payment_complete' or 'kernel_expired' state.
    Transitions the order to 'human_kernel_required'.
    
    Returns the session with the token (show this once to the human).
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(hours=SESSION_TTL_HOURS)
    
    token = secrets.token_urlsafe(TOKEN_BYTES)
    
    kernel_session = HumanKernelSession(
        order_id=order.id,
        token=token,
        expires_at=expires_at,
        status="pending",
        completed_steps=[],
    )
    session.add(kernel_session)
    
    # Transition order state
    await transition_order(
        session, order, OrderState.HUMAN_KERNEL_REQUIRED,
        actor=actor,
        details={"kernel_session_token_prefix": token[:8]},
    )
    
    await session.flush()
    return kernel_session


async def get_session_by_token(
    session: AsyncSession,
    token: str,
) -> HumanKernelSession | None:
    """Look up a kernel session by its token.
    
    Returns None if not found or expired.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    
    result = await session.execute(
        select(HumanKernelSession).where(
            HumanKernelSession.token == token,
        )
    )
    kernel_session = result.scalar_one_or_none()
    
    if kernel_session is None:
        return None
    
    # Check expiry
    if kernel_session.expires_at < now and kernel_session.status != "completed":
        kernel_session.status = "expired"
        return kernel_session
    
    return kernel_session


async def complete_step(
    session: AsyncSession,
    kernel_session: HumanKernelSession,
    step: str,
    *,
    ip_address: str | None = None,
) -> HumanKernelSession:
    """Mark a step as completed in the kernel session.
    
    Valid steps: pii_collection, kyc_verification, document_signing, attestation
    """
    if step not in KERNEL_STEPS:
        raise ValueError(f"Invalid step: {step!r}. Valid: {KERNEL_STEPS}")
    
    if kernel_session.status == "expired":
        raise ValueError("Session has expired")
    
    if step in kernel_session.completed_steps:
        return kernel_session  # idempotent
    
    # Update status
    if kernel_session.status == "pending":
        kernel_session.status = "in_progress"
    
    # Append step (copy list for SQLAlchemy mutation detection)
    kernel_session.completed_steps = [*kernel_session.completed_steps, step]
    kernel_session.ip_address = ip_address
    
    # Audit
    audit = AuditEvent(
        order_id=kernel_session.order_id,
        actor=f"human_kernel:{kernel_session.token[:8]}",
        action=f"kernel_step_completed:{step}",
        details={"step": step, "completed_steps": kernel_session.completed_steps},
        ip_address=ip_address,
    )
    session.add(audit)
    
    # Check if all steps are done
    if all(s in kernel_session.completed_steps for s in KERNEL_STEPS):
        kernel_session.status = "completed"
        kernel_session.completed_at = datetime.datetime.now(datetime.timezone.utc)
    
    return kernel_session


async def complete_kernel(
    session: AsyncSession,
    kernel_session: HumanKernelSession,
    order: EntityOrder,
    *,
    actor: str = "system",
) -> EntityOrder:
    """Finalize the kernel session and transition the order.
    
    Only callable when all kernel steps are completed.
    """
    if kernel_session.status != "completed":
        raise ValueError(
            f"Kernel session not complete. Status: {kernel_session.status!r}, "
            f"completed steps: {kernel_session.completed_steps}"
        )
    
    return await transition_order(
        session, order, OrderState.HUMAN_KERNEL_COMPLETED,
        actor=actor,
        details={"kernel_session_id": str(kernel_session.id)},
    )
