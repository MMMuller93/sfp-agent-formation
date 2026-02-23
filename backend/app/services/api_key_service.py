"""API key management: creation, validation, and hashing."""

from __future__ import annotations

import hashlib
import secrets
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ApiKey, AuditEvent


def generate_api_key() -> str:
    """Generate a new API key in the format 'sfp_live_xxxxx'."""
    random_part = secrets.token_urlsafe(32)
    return f"sfp_live_{random_part}"


def hash_api_key(key: str) -> str:
    """SHA-256 hash of the full API key."""
    return hashlib.sha256(key.encode()).hexdigest()


def get_key_prefix(key: str) -> str:
    """First 8 characters for display/identification."""
    return key[:8]


async def create_api_key(
    session: AsyncSession,
    name: str,
    scopes: list[str] | None = None,
) -> tuple[ApiKey, str]:
    """Create a new API key. Returns (db record, plaintext key).

    The plaintext key is returned ONLY at creation time — it's not
    stored in the database. The caller must show it to the user.
    """
    raw_key = generate_api_key()

    api_key = ApiKey(
        key_hash=hash_api_key(raw_key),
        key_prefix=get_key_prefix(raw_key),
        name=name,
        scopes=scopes or ["*"],
        active=True,
    )
    session.add(api_key)

    audit = AuditEvent(
        actor="system",
        action="api_key_created",
        details={"key_prefix": api_key.key_prefix, "name": name, "scopes": api_key.scopes},
    )
    session.add(audit)

    await session.flush()
    return api_key, raw_key


async def validate_api_key(
    session: AsyncSession,
    raw_key: str,
) -> ApiKey | None:
    """Validate an API key and return the record if valid, None otherwise."""
    key_hash = hash_api_key(raw_key)

    result = await session.execute(
        select(ApiKey).where(
            ApiKey.key_hash == key_hash,
            ApiKey.active == True,  # noqa: E712
        )
    )
    api_key = result.scalar_one_or_none()

    if api_key is not None:
        # Update last_used_at
        from sqlalchemy import func
        api_key.last_used_at = func.now()

    return api_key


async def revoke_api_key(
    session: AsyncSession,
    key_id: UUID,
) -> bool:
    """Deactivate an API key. Returns True if found and deactivated."""
    result = await session.execute(
        select(ApiKey).where(ApiKey.id == key_id)
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        return False

    api_key.active = False

    audit = AuditEvent(
        actor="system",
        action="api_key_revoked",
        details={"key_prefix": api_key.key_prefix, "key_id": str(key_id)},
    )
    session.add(audit)

    return True
