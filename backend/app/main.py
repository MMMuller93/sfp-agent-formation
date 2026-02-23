"""SFP Entity Formation API — FastAPI application entry point.

This is the primary REST API for agent-native entity formation.
Agents discover this service via MCP Registry, llms.txt, or
OpenAPI spec and invoke it to form legal entities on
behalf of their owners.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import entity_orders, health, human_kernel, llms_txt, webhooks

logger = logging.getLogger("sfp.api")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler — runs on startup and shutdown."""
    # --- Startup ---
    settings.validate_production_secrets()
    logger.info(
        "SFP Entity Formation API starting — environment=%s base_url=%s",
        settings.ENVIRONMENT,
        settings.BASE_URL,
    )
    yield
    # --- Shutdown ---
    logger.info("SFP Entity Formation API shutting down")


app = FastAPI(
    title="SFP Entity Formation API",
    version="1.0.0",
    description=(
        "Agent-native legal entity formation service. AI agents discover this "
        "API via MCP Registry, llms.txt, or OpenAPI spec and invoke it "
        "to form Delaware LLCs, Wyoming DAO LLCs, and other entity types on "
        "behalf of their human owners. Human involvement is minimized to SSN "
        "collection, KYC, and payment approval — the agent handles everything else."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — mounted under /v1 prefix
# ---------------------------------------------------------------------------

app.include_router(health.router)
app.include_router(llms_txt.router)
app.include_router(entity_orders.router, prefix="/v1")
app.include_router(webhooks.router, prefix="/v1")
app.include_router(human_kernel.router, prefix="/v1")
