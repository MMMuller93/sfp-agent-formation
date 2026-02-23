"""API key authentication middleware for FastAPI.

Extracts the API key from the X-API-Key header, validates it against
the database, and injects the authenticated ApiKey record into the
request state.

Routes that need authentication use the ``require_api_key`` dependency.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ApiKey
from app.services.api_key_service import validate_api_key

# FastAPI security scheme — declares X-API-Key header in OpenAPI
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_api_key(
    api_key_header: Optional[str] = Security(_api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Optional[ApiKey]:
    """Extract and validate the API key from the request header.

    Returns the ApiKey record if valid, None if no key provided.
    """
    if api_key_header is None:
        return None

    api_key = await validate_api_key(db, api_key_header)
    return api_key


async def require_api_key(
    api_key: Optional[ApiKey] = Depends(get_current_api_key),
) -> ApiKey:
    """Dependency that requires a valid API key.

    Use this on any route that needs authentication::

        @router.get("/protected")
        async def protected(api_key: ApiKey = Depends(require_api_key)):
            ...
    """
    if api_key is None:
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid API key. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


def check_scope(api_key: ApiKey, required_scope: str) -> bool:
    """Check if an API key has the required scope.

    Wildcard ``"*"`` grants access to everything.
    """
    if "*" in api_key.scopes:
        return True
    return required_scope in api_key.scopes


async def require_scope(scope: str):
    """Factory for scope-checking dependencies.

    Usage::

        @router.post("/admin-action")
        async def admin_action(
            api_key: ApiKey = Depends(require_api_key),
            _: None = Depends(require_scope("admin")),
        ):
            ...
    """
    async def _check(api_key: ApiKey = Depends(require_api_key)):
        if not check_scope(api_key, scope):
            raise HTTPException(
                status_code=403,
                detail=f"API key lacks required scope: {scope}",
            )
    return Depends(_check)
