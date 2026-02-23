"""
SFP Entity Formation — MCP Tool Server

Exposes entity formation capabilities to AI agents via the Model Context Protocol.
Connects to the SFP Formation API backend over HTTP.

Usage:
    python server.py

Configuration:
    SFP_API_BASE_URL  — Base URL of the SFP Formation API (default: http://localhost:8000)
    SFP_API_KEY       — API key for authenticating with the SFP backend
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_BASE_URL = os.environ.get("SFP_API_BASE_URL", "http://localhost:8000")
API_KEY = os.environ.get("SFP_API_KEY", "")

# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


def _client() -> httpx.AsyncClient:
    """Build an async HTTP client pointed at the SFP Formation API."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    return httpx.AsyncClient(
        base_url=API_BASE_URL,
        headers=headers,
        timeout=30.0,
    )


async def _api_request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    """Make an authenticated request to the SFP API and return the JSON body."""
    async with _client() as client:
        response = await client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json()


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "SFP Entity Formation",
    description=(
        "AI-agent-native legal entity formation service. "
        "Form LLCs, DAOs, corps, and trusts across US jurisdictions."
    ),
)

# ---------------------------------------------------------------------------
# Tool: create_entity_order
# ---------------------------------------------------------------------------


class CreateEntityOrderParams(BaseModel):
    jurisdiction: str = Field(description="Two-letter state code (e.g. DE, WY, NV)")
    vehicle_type: str = Field(description="Entity type: LLC, DAO_LLC, C_CORP, S_CORP, LP, STATUTORY_TRUST, SERIES_LLC")
    entity_name: str = Field(description="Desired entity name including suffix (e.g. 'Acme Holdings LLC')")
    member_name: str = Field(description="Full legal name of the organizing member")
    member_email: str = Field(description="Email address for the organizing member")


@mcp.tool()
async def create_entity_order(
    jurisdiction: str,
    vehicle_type: str,
    entity_name: str,
    member_name: str,
    member_email: str,
) -> dict[str, Any]:
    """Create a new entity formation order.

    Initiates the formation process for a legal entity in the specified
    jurisdiction. The order enters the 'draft' state and progresses through
    compliance review, document generation, and state filing.

    Returns the created order with its ID, current state, and next steps.
    """
    payload = CreateEntityOrderParams(
        jurisdiction=jurisdiction,
        vehicle_type=vehicle_type,
        entity_name=entity_name,
        member_name=member_name,
        member_email=member_email,
    )
    return await _api_request("POST", "/v1/entity-orders", json=payload.model_dump())


# ---------------------------------------------------------------------------
# Tool: check_name_availability
# ---------------------------------------------------------------------------


@mcp.tool()
async def check_name_availability(
    jurisdiction: str,
    entity_name: str,
) -> dict[str, Any]:
    """Check whether an entity name is available in a jurisdiction.

    Queries the state's business name registry (via API or automated portal
    check) to determine if the proposed name is available for registration.

    Returns availability status, any conflicts found, and suggested
    alternatives if the name is taken.
    """
    return await _api_request(
        "POST",
        "/v1/name-check",
        json={"jurisdiction": jurisdiction, "entity_name": entity_name},
    )


# ---------------------------------------------------------------------------
# Tool: get_entity_status
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_entity_status(
    order_id: str,
) -> dict[str, Any]:
    """Get the current status of an entity formation order.

    Returns the full order details including current state, timeline of
    state transitions, generated documents, filing status, and any
    action items that require attention.
    """
    return await _api_request("GET", f"/v1/entity-orders/{order_id}")


# ---------------------------------------------------------------------------
# Tool: start_human_kernel
# ---------------------------------------------------------------------------


@mcp.tool()
async def start_human_kernel(
    order_id: str,
) -> dict[str, Any]:
    """Initiate a human-in-the-loop review for an entity order.

    Triggers a human kernel session for tasks that require manual
    intervention, such as CAPTCHA solving during state portal filing,
    compliance review of flagged orders, or document verification.

    Returns the kernel session ID and a webhook URL for receiving
    the human operator's response.
    """
    return await _api_request("POST", f"/v1/entity-orders/{order_id}/human-kernel")


# ---------------------------------------------------------------------------
# Tool: list_available_vehicles
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_available_vehicles() -> dict[str, Any]:
    """List all entity vehicle types available for formation.

    Returns the supported entity types (LLC, DAO LLC, C-Corp, etc.)
    grouped by jurisdiction, including formation fees, typical
    processing times, and any jurisdiction-specific requirements.
    """
    return await _api_request("GET", "/v1/vehicles")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
