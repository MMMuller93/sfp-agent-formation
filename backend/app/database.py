"""SQLAlchemy async engine and session factories.

Two separate database connections are maintained:

1. **Main database** — entity orders, documents, agent configs, audit logs.
2. **PII vault database** — encrypted SSN/ITIN and other personally
   identifiable information, physically isolated from the application DB.

Both use asyncpg as the async driver.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

# Re-export Base from models so that consumers can import from either
# app.database or app.models — both refer to the same metadata.
from app.models import Base  # noqa: F401

settings = get_settings()

# ---------------------------------------------------------------------------
# Engines
# ---------------------------------------------------------------------------

main_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(not settings.is_production),
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
)

pii_vault_engine = create_async_engine(
    settings.PII_VAULT_DATABASE_URL,
    echo=False,  # Never log PII vault queries
    pool_size=5,
    max_overflow=5,
    pool_pre_ping=True,
    pool_recycle=300,
)

# ---------------------------------------------------------------------------
# Session factories
# ---------------------------------------------------------------------------

MainSessionLocal = async_sessionmaker(
    bind=main_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

PIIVaultSessionLocal = async_sessionmaker(
    bind=pii_vault_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ---------------------------------------------------------------------------
# PII vault base (separate metadata from main models)
# ---------------------------------------------------------------------------


class PIIBase(DeclarativeBase):
    """Declarative base for PII vault models (separate metadata)."""


# ---------------------------------------------------------------------------
# Dependency injection helpers
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session for the main application database.

    Usage with FastAPI::

        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with MainSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_pii_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session for the PII vault database.

    This session is intentionally separate from the main DB to enforce
    a physical isolation boundary around personally identifiable data.
    """
    async with PIIVaultSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
