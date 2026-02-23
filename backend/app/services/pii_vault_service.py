"""PII vault service — development stub.

In production, this connects to a physically isolated PostgreSQL database
with envelope encryption (AES-256-GCM). In development, it stores
values in-memory with a simple prefix for identification.

The interface uses opaque 'vault_ref' strings — the main application
database never sees raw PII.

SECURITY NOTE: This stub stores PII in plaintext in memory.
It MUST be replaced with the real vault before production deployment.
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

import logging

logger = logging.getLogger("sfp.pii_vault")

# In-memory store for development
_DEV_STORE: dict[str, Any] = {}


def _generate_ref() -> str:
    """Generate an opaque vault reference."""
    return f"vault_{secrets.token_urlsafe(16)}"


async def store_ssn(ssn: str, *, order_id: str | None = None) -> str:
    """Store an SSN and return an opaque vault reference.
    
    In production: encrypts with DEK, stores DEK encrypted with KEK.
    In dev: stores in memory.
    """
    ref = _generate_ref()
    _DEV_STORE[ref] = {
        "type": "ssn",
        "value": ssn,
        "order_id": order_id,
        "hash": hashlib.sha256(ssn.encode()).hexdigest()[:8],  # for audit only
    }
    logger.warning("DEV STUB: SSN stored in memory at %s (NOT encrypted)", ref)
    return ref


async def store_address(address: dict[str, str], *, order_id: str | None = None) -> str:
    """Store an address and return an opaque vault reference."""
    ref = _generate_ref()
    _DEV_STORE[ref] = {
        "type": "address",
        "value": address,
        "order_id": order_id,
    }
    logger.warning("DEV STUB: Address stored in memory at %s (NOT encrypted)", ref)
    return ref


async def store_dob(dob: str, *, order_id: str | None = None) -> str:
    """Store a date of birth and return an opaque vault reference."""
    ref = _generate_ref()
    _DEV_STORE[ref] = {
        "type": "dob",
        "value": dob,
        "order_id": order_id,
    }
    logger.warning("DEV STUB: DOB stored in memory at %s (NOT encrypted)", ref)
    return ref


async def retrieve(ref: str) -> Any | None:
    """Retrieve a value by its vault reference.
    
    Returns None if the reference is not found.
    In production, decrypts with KEK -> DEK -> plaintext.
    """
    entry = _DEV_STORE.get(ref)
    if entry is None:
        return None
    return entry["value"]


async def delete(ref: str) -> bool:
    """Delete a value from the vault. Returns True if found and deleted."""
    if ref in _DEV_STORE:
        del _DEV_STORE[ref]
        return True
    return False


async def exists(ref: str) -> bool:
    """Check if a vault reference exists (without retrieving the value)."""
    return ref in _DEV_STORE
