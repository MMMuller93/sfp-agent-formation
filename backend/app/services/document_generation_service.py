"""Document generation orchestration service.

Coordinates the rendering of all required formation documents for an
entity order. Each document type has a specific template and context
builder.

Documents generated for a DE LLC formation:
1. Certificate of Formation
2. Operating Agreement (with Agent Authority Schedule exhibit)
3. Agent Authority Schedule
4. Form SS-4 (EIN application)
5. Banking Resolution

For WY DAO LLC, adds:
6. Articles of Organization (DAO designation)
7. Smart Contract Identifier Schedule
"""

from __future__ import annotations

import datetime
import hashlib
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent, Document, EntityOrder
from app.services.state_machine import OrderState, transition_order

logger = logging.getLogger("sfp.docgen")

# Output directory for generated documents
OUTPUT_BASE = Path(__file__).resolve().parents[3] / "generated_docs"

# Document types required per vehicle type
REQUIRED_DOCS: dict[str, list[str]] = {
    "llc": [
        "certificate_of_formation",
        "operating_agreement",
        "agent_authority_schedule",
        "form_ss4",
        "banking_resolution",
    ],
    "dao_llc": [
        "articles_of_organization",
        "operating_agreement",
        "agent_authority_schedule",
        "smart_contract_schedule",
        "form_ss4",
        "banking_resolution",
    ],
    "corporation": [
        "certificate_of_incorporation",
        "bylaws",
        "form_ss4",
        "banking_resolution",
    ],
}

# Map document type to template file
DOC_TEMPLATES: dict[str, dict[str, str]] = {
    "certificate_of_formation": {
        "de_llc": "certificate_of_formation.docx",
    },
    "operating_agreement": {
        "de_llc": "operating_agreement.docx",
        "wy_dao_llc": "operating_agreement_dao.docx",
    },
    "agent_authority_schedule": {
        "de_llc": "agent_authority_schedule.docx",
        "wy_dao_llc": "agent_authority_schedule.docx",
    },
    "articles_of_organization": {
        "wy_dao_llc": "articles_of_organization.docx",
    },
    "smart_contract_schedule": {
        "wy_dao_llc": "smart_contract_schedule.docx",
    },
    "form_ss4": {
        "de_llc": "form_ss4.docx",
        "wy_dao_llc": "form_ss4.docx",
    },
    "banking_resolution": {
        "de_llc": "banking_resolution.docx",
        "wy_dao_llc": "banking_resolution.docx",
    },
}


def _resolve_jurisdiction_key(jurisdiction: str, vehicle_type: str) -> str:
    """Map jurisdiction + vehicle_type to template directory name."""
    mapping = {
        ("DE", "llc"): "de_llc",
        ("DE", "corporation"): "de_llc",  # reuse DE templates
        ("WY", "dao_llc"): "wy_dao_llc",
        ("WY", "llc"): "de_llc",  # WY LLC uses DE templates for now
    }
    return mapping.get((jurisdiction.upper(), vehicle_type), "de_llc")


def build_document_context(order: EntityOrder) -> dict[str, Any]:
    """Build the template rendering context from an entity order.

    This extracts all the data needed by templates from the ORM model
    and its relationships.
    """
    # Get members by role
    members = [p for p in order.persons if p.role == "member"]
    managers = [p for p in order.persons if p.role == "manager"]
    responsible_party = next(
        (p for p in order.persons if p.role == "responsible_party"),
        members[0] if members else None,
    )

    # Get agent if any
    agent = order.agents[0] if order.agents else None

    now = datetime.datetime.now(datetime.timezone.utc)

    context = {
        # Entity info
        "entity_name": order.formatted_name or order.requested_name,
        "entity_type": order.vehicle_type.upper(),
        "jurisdiction": order.jurisdiction,
        "jurisdiction_full": {
            "DE": "Delaware",
            "WY": "Wyoming",
            "NV": "Nevada",
        }.get(order.jurisdiction, order.jurisdiction),
        "formation_date": now.strftime("%B %d, %Y"),
        "formation_year": str(now.year),
        # Members
        "members": [
            {
                "name": m.legal_name,
                "email": m.email or "",
                "role": m.role,
                "ownership_percentage": m.ownership_percentage or 0,
            }
            for m in members
        ],
        "managers": [
            {
                "name": m.legal_name,
                "email": m.email or "",
            }
            for m in managers
        ],
        "member_count": len(members),
        "is_single_member": len(members) == 1,
        "is_manager_managed": len(managers) > 0,
        # Responsible party (for SS-4)
        "responsible_party_name": (
            responsible_party.legal_name
            if responsible_party
            else "[RESPONSIBLE PARTY]"
        ),
        "responsible_party_title": (
            "Managing Member" if responsible_party else "[TITLE]"
        ),
        # Agent
        "has_agent": agent is not None,
        "agent_name": agent.display_name if agent else "",
        "agent_authority_scope": agent.authority_scope if agent else {},
        "agent_transaction_limit": (
            agent.transaction_limit_cents if agent else 0
        ),
        "agent_smart_contract": (
            agent.smart_contract_address if agent else ""
        ),
        # Registered agent (placeholder)
        "registered_agent_name": "[ATTORNEY: REVIEW AND REPLACE]",
        "registered_agent_address": "[ATTORNEY: REVIEW AND REPLACE]",
        # Meta
        "order_id": str(order.id),
        "generated_at": now.isoformat(),
    }

    return context


async def generate_formation_documents(
    session: AsyncSession,
    order: EntityOrder,
    *,
    actor: str = "system",
) -> list[Document]:
    """Generate all required formation documents for an order.

    Creates Document records in the database and returns them.
    The order must be in human_kernel_completed state.
    Templates must exist — if they don't, the document is skipped
    with a warning.
    """
    from app.services.template_engine import get_template_path, render_document

    jurisdiction_key = _resolve_jurisdiction_key(
        order.jurisdiction, order.vehicle_type
    )
    required = REQUIRED_DOCS.get(order.vehicle_type, REQUIRED_DOCS["llc"])
    context = build_document_context(order)

    output_dir = OUTPUT_BASE / str(order.id)
    output_dir.mkdir(parents=True, exist_ok=True)

    documents: list[Document] = []

    for doc_type in required:
        # Find the template
        templates = DOC_TEMPLATES.get(doc_type, {})
        template_name = templates.get(jurisdiction_key)

        if template_name is None:
            logger.warning(
                "No template for doc_type=%s jurisdiction=%s — skipping",
                doc_type,
                jurisdiction_key,
            )
            continue

        # Check if template file exists
        try:
            get_template_path(jurisdiction_key, template_name)
        except FileNotFoundError:
            logger.warning(
                "Template file not found: %s/%s — creating placeholder Document record",
                jurisdiction_key,
                template_name,
            )
            # Create a placeholder document record
            doc = Document(
                order_id=order.id,
                doc_type=doc_type,
                template_version="no_template",
                file_ref=f"pending/{order.id}/{doc_type}.docx",
                file_hash="0" * 64,
                signing_status="unsigned",
            )
            session.add(doc)
            documents.append(doc)
            continue

        # Render the document
        output_path = output_dir / f"{doc_type}.docx"
        try:
            result = render_document(
                jurisdiction_key,
                template_name,
                context,
                output_path,
            )

            doc = Document(
                order_id=order.id,
                doc_type=doc_type,
                template_version=result["template_version"],
                file_ref=str(result["output_path"]),
                file_hash=result["file_hash"],
                signing_status="unsigned",
            )
            session.add(doc)
            documents.append(doc)

        except Exception as e:
            logger.error(
                "Failed to render %s for order %s: %s",
                doc_type,
                order.id,
                e,
            )
            # Create a failed document record
            doc = Document(
                order_id=order.id,
                doc_type=doc_type,
                template_version="render_failed",
                file_ref=f"failed/{order.id}/{doc_type}.docx",
                file_hash="0" * 64,
                signing_status="unsigned",
            )
            session.add(doc)
            documents.append(doc)

    # Audit
    audit = AuditEvent(
        order_id=order.id,
        actor=actor,
        action="documents_generated",
        details={
            "document_count": len(documents),
            "doc_types": [d.doc_type for d in documents],
            "jurisdiction_key": jurisdiction_key,
        },
    )
    session.add(audit)

    # Transition order state
    await transition_order(
        session,
        order,
        OrderState.DOCS_GENERATED,
        actor=actor,
        details={"document_count": len(documents)},
    )

    await session.flush()
    return documents
