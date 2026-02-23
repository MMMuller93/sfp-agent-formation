"""Centralized audit logging service.

Every mutation in the system should create an AuditEvent record.
This service provides helpers to make that easy and consistent.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent


async def log_event(
    session: AsyncSession,
    *,
    action: str,
    actor: str = "system",
    order_id: UUID | None = None,
    details: dict[str, Any] | None = None,
    artifact_hash: str | None = None,
    ip_address: str | None = None,
) -> AuditEvent:
    """Create and persist an audit event.
    
    Args:
        session: Database session (caller commits).
        action: Machine-readable action name (e.g., 'order_created', 'state_transition:draft->intake_complete').
        actor: Who performed the action (e.g., 'system', 'api_key:sfp_live', 'human_kernel:abc123').
        order_id: Optional associated entity order.
        details: Optional JSONB payload with event specifics.
        artifact_hash: Optional SHA-256 of any generated artifact.
        ip_address: Optional IP address of the caller.
    
    Returns:
        The created AuditEvent (not yet committed).
    """
    event = AuditEvent(
        order_id=order_id,
        actor=actor,
        action=action,
        details=details,
        artifact_hash=artifact_hash,
        ip_address=ip_address,
    )
    session.add(event)
    return event


async def get_audit_trail(
    session: AsyncSession,
    order_id: UUID,
    *,
    limit: int = 100,
) -> list[AuditEvent]:
    """Get the audit trail for a specific order, newest first."""
    from sqlalchemy import select
    
    result = await session.execute(
        select(AuditEvent)
        .where(AuditEvent.order_id == order_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
