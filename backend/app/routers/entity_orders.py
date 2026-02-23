"""Entity order endpoints.

Handles the full lifecycle of entity formation orders: creation,
status queries, name checks, document generation, filing, and
post-formation workflows (EIN, banking intro).
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post(
    "",
    summary="Create entity formation order",
    description="Start a new entity formation. Returns entity_id and initial status.",
    status_code=201,
)
async def create_entity() -> dict[str, str]:
    return {"status": "not_implemented", "message": "Entity creation endpoint — implementation pending"}


@router.get(
    "/{entity_id}",
    summary="Get entity status",
    description="Returns current status and next required action for an entity order.",
)
async def get_entity(entity_id: str) -> dict[str, str]:
    return {"entity_id": entity_id, "status": "not_implemented"}


@router.patch(
    "/{entity_id}",
    summary="Update entity details",
    description="Update entity details before filing (e.g., name, agent config).",
)
async def update_entity(entity_id: str) -> dict[str, str]:
    return {"entity_id": entity_id, "status": "not_implemented"}


@router.post(
    "/{entity_id}/name-check",
    summary="Check name availability",
    description="Check whether the entity name is available in the target jurisdiction.",
)
async def name_check(entity_id: str) -> dict[str, str]:
    return {"entity_id": entity_id, "status": "not_implemented"}


@router.post(
    "/{entity_id}/documents",
    summary="Generate formation documents",
    description="Generate operating agreement, certificate of formation, and Agent Authority Schedule.",
)
async def generate_documents(entity_id: str) -> dict[str, str]:
    return {"entity_id": entity_id, "status": "not_implemented"}


@router.get(
    "/{entity_id}/documents/{document_id}",
    summary="Download document",
    description="Download a specific formation document.",
)
async def get_document(entity_id: str, document_id: str) -> dict[str, str]:
    return {"entity_id": entity_id, "document_id": document_id, "status": "not_implemented"}


@router.post(
    "/{entity_id}/file",
    summary="Submit state filing",
    description="Submit formation documents to the state for filing.",
)
async def file_entity(entity_id: str) -> dict[str, str]:
    return {"entity_id": entity_id, "status": "not_implemented"}


@router.post(
    "/{entity_id}/ein",
    summary="Start EIN application",
    description="Initiate IRS EIN application for the formed entity.",
)
async def apply_ein(entity_id: str) -> dict[str, str]:
    return {"entity_id": entity_id, "status": "not_implemented"}


@router.post(
    "/{entity_id}/banking-intro",
    summary="Trigger banking introduction",
    description="Send pre-filled banking application to partner bank (Mercury/Relay).",
)
async def banking_intro(entity_id: str) -> dict[str, str]:
    return {"entity_id": entity_id, "status": "not_implemented"}


@router.get(
    "",
    summary="List jurisdictions",
    description="List available jurisdictions with pricing, timelines, and requirements.",
)
async def list_jurisdictions() -> dict[str, list[dict[str, str]]]:
    return {
        "jurisdictions": [
            {
                "code": "DE",
                "name": "Delaware LLC",
                "price": "$499",
                "timeline": "1-3 business days",
                "description": "Standard Delaware LLC — default recommendation for most agent use cases.",
            },
            {
                "code": "WY_DAO",
                "name": "Wyoming DAO LLC",
                "price": "$699",
                "timeline": "2-5 business days",
                "description": "Wyoming DAO LLC with algorithmically managed provisions. Requires operational smart contract.",
            },
            {
                "code": "MI",
                "name": "Marshall Islands DAO LLC",
                "price": "$4,999",
                "timeline": "2-4 weeks",
                "description": "Offshore DAO LLC via MIDAO partnership. Crypto-native governance.",
            },
        ]
    }
