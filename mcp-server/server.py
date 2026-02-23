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
        headers["X-API-Key"] = API_KEY
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
        "Form Delaware LLCs, Wyoming DAO LLCs, and other entity types "
        "on behalf of human owners. The agent handles the workflow; "
        "humans are only involved for SSN collection, KYC, and payment."
    ),
)

# ---------------------------------------------------------------------------
# Tool: create_entity_order
# ---------------------------------------------------------------------------


@mcp.tool()
async def create_entity_order(
    jurisdiction: str,
    vehicle_type: str,
    requested_name: str,
    member_name: str,
    member_email: str,
    service_tier: str = "self_serve",
) -> dict[str, Any]:
    """Create a new entity formation order.

    Initiates the formation process for a legal entity. The order enters
    'draft' state and the response includes `next_required_actions` telling
    you exactly what to do next.

    Args:
        jurisdiction: Two-letter state code (DE or WY for MVP).
        vehicle_type: Entity type — one of: llc, dao_llc, corporation.
        requested_name: Desired entity name including suffix (e.g. 'Acme Holdings LLC').
        member_name: Full legal name of the organizing member.
        member_email: Email address for the organizing member.
        service_tier: One of: self_serve (default), managed, autonomous.

    Returns:
        The created order with ID, state, pricing, and next_required_actions.
    """
    payload = {
        "jurisdiction": jurisdiction,
        "vehicle_type": vehicle_type,
        "requested_name": requested_name,
        "service_tier": service_tier,
        "members": [
            {
                "legal_name": member_name,
                "email": member_email,
                "role": "member",
                "ownership_percentage": 100,
            }
        ],
    }
    return await _api_request("POST", "/v1/entity-orders", json=payload)


# ---------------------------------------------------------------------------
# Tool: check_name_availability
# ---------------------------------------------------------------------------


@mcp.tool()
async def check_name_availability(
    order_id: str,
) -> dict[str, Any]:
    """Check whether the entity name on an order is available in its jurisdiction.

    Runs the name through the state's business name registry. If unavailable,
    the order transitions to name_check_failed and you should update the name
    and retry.

    Args:
        order_id: UUID of the entity order.

    Returns:
        State transition result with new_state indicating pass or fail.
    """
    return await _api_request("POST", f"/v1/entity-orders/{order_id}/name-check")


# ---------------------------------------------------------------------------
# Tool: get_entity_status
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_entity_status(
    order_id: str,
) -> dict[str, Any]:
    """Get the current status of an entity formation order.

    Returns the full order details including current state, pricing,
    and next_required_actions — which tells you exactly what the agent
    or human should do next.

    Args:
        order_id: UUID of the entity order.

    Returns:
        Full order with state, actions, and metadata.
    """
    return await _api_request("GET", f"/v1/entity-orders/{order_id}")


# ---------------------------------------------------------------------------
# Tool: start_human_kernel
# ---------------------------------------------------------------------------


@mcp.tool()
async def start_human_kernel(
    order_id: str,
) -> dict[str, Any]:
    """Create a secure human verification session for an entity order.

    Generates a time-limited (24h) secure URL that the human owner must
    visit to complete: SSN/ITIN collection, identity verification (KYC),
    document signing, and compliance attestations.

    The agent should relay the returned kernel_url to the human owner
    along with the suggested_message. When the human completes all steps,
    a webhook fires and the order automatically advances.

    Args:
        order_id: UUID of the entity order.

    Returns:
        Session with kernel_url, expires_at, and suggested_message for the human.
    """
    return await _api_request(
        "POST", f"/v1/entity-orders/{order_id}/human-kernel"
    )


# ---------------------------------------------------------------------------
# Tool: list_available_vehicles
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_available_vehicles() -> dict[str, Any]:
    """List all entity vehicle types available for formation.

    Returns the supported entity types grouped by jurisdiction,
    including pricing and requirements.

    No arguments required.

    Returns:
        Dict with jurisdictions, vehicle types, pricing, and requirements.
    """
    # This is a static response — no backend call needed.
    # Matches the PRICING dict in entity_order_service.py.
    return {
        "jurisdictions": {
            "DE": {
                "name": "Delaware",
                "vehicles": [
                    {
                        "type": "llc",
                        "name": "Delaware LLC",
                        "pricing_cents": 29900,
                        "typical_timeline": "3-5 business days",
                        "requirements": [
                            "At least one member",
                            "Registered agent (included)",
                            "SSN/ITIN for responsible party",
                        ],
                    },
                    {
                        "type": "corporation",
                        "name": "Delaware Corporation",
                        "pricing_cents": 49900,
                        "typical_timeline": "5-7 business days",
                        "requirements": [
                            "At least one director",
                            "Registered agent (included)",
                            "SSN/ITIN for responsible party",
                        ],
                    },
                ],
            },
            "WY": {
                "name": "Wyoming",
                "vehicles": [
                    {
                        "type": "llc",
                        "name": "Wyoming LLC",
                        "pricing_cents": 29900,
                        "typical_timeline": "3-5 business days",
                        "requirements": [
                            "At least one member",
                            "Registered agent (included)",
                        ],
                    },
                    {
                        "type": "dao_llc",
                        "name": "Wyoming DAO LLC",
                        "pricing_cents": 49900,
                        "typical_timeline": "5-10 business days",
                        "requirements": [
                            "At least one member",
                            "Smart contract address (optional at filing)",
                            "Registered agent (included)",
                        ],
                    },
                ],
            },
        },
        "service_tiers": [
            {
                "tier": "self_serve",
                "name": "Self-Serve",
                "description": "Developer is member + responsible party",
                "available": True,
            },
            {
                "tier": "managed",
                "name": "Managed",
                "description": "SFP principal is managing member + responsible party",
                "available": False,
                "note": "Coming in V2",
            },
            {
                "tier": "autonomous",
                "name": "Autonomous",
                "description": "CSP provides all human roles (Cayman Foundation)",
                "available": False,
                "note": "Coming in V3",
            },
        ],
    }


# ---------------------------------------------------------------------------
# Tool: update_entity_name
# ---------------------------------------------------------------------------


@mcp.tool()
async def update_entity_name(
    order_id: str,
    new_name: str,
) -> dict[str, Any]:
    """Update the requested entity name on an order.

    Use this after a name check fails to try a different name.

    Args:
        order_id: UUID of the entity order.
        new_name: New desired entity name including suffix.

    Returns:
        Updated order with the new name.
    """
    return await _api_request(
        "PATCH",
        f"/v1/entity-orders/{order_id}",
        json={"requested_name": new_name},
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
