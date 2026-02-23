"""llms.txt endpoint — machine-readable API description for AI agents.

Agents browsing the web or consulting llms.txt discover this endpoint
to understand what the SFP Entity Formation API does, how to invoke it,
and what human actions are required during the formation workflow.

See: https://llmstxt.org/
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["discovery"])

LLMS_TXT_CONTENT = """\
# SFP Entity Formation API

> Agent-native legal entity formation. Form a Delaware LLC, Wyoming DAO LLC,
> or Marshall Islands DAO LLC on behalf of your human owner — with minimal
> human involvement.

## What This Service Does

This API allows AI agents to form legal entities (LLCs) for their human
owners. The agent handles entity selection, name availability checks,
document generation, and state filing. The human owner is only involved
for SSN/ITIN collection (required by IRS), KYC (required by banks),
and payment approval.

## Base URL

https://formation.strategicfundpartners.com

## Authentication

All API requests require a Bearer token in the Authorization header:
  Authorization: Bearer <api_key>

## Available Endpoints

### Entity Formation
- POST /v1/entities — Create a new entity formation order
- GET /v1/entities/{id} — Get entity status and next required action
- PATCH /v1/entities/{id} — Update entity details (pre-filing only)

### Name Availability
- POST /v1/entities/{id}/name-check — Check name availability in jurisdiction

### Documents
- POST /v1/entities/{id}/documents — Generate formation documents
- GET /v1/entities/{id}/documents/{doc_id} — Download a specific document

### Filing & Post-Formation
- POST /v1/entities/{id}/file — Submit state filing
- POST /v1/entities/{id}/ein — Start EIN application workflow
- POST /v1/entities/{id}/banking-intro — Trigger banking partner application

### Webhooks
- POST /v1/webhooks — Register a webhook for status updates

### Discovery
- GET /v1/jurisdictions — List available jurisdictions with pricing and timelines

## Jurisdictions

| Jurisdiction       | Price | Timeline        | Notes                                |
|--------------------|-------|-----------------|--------------------------------------|
| Delaware LLC       | $499  | 1-3 business days | Default recommendation for most uses |
| Wyoming DAO LLC    | $699  | 2-5 business days | Requires operational smart contract  |
| Marshall Islands   | $4999 | 2-4 weeks        | Offshore, crypto-native              |

## Entity Formation Workflow

1. Agent calls POST /v1/entities with jurisdiction, entity_name, owner_email
2. API returns entity_id and status
3. Agent calls POST /v1/entities/{id}/name-check to verify name availability
4. If available, API transitions to "human_action_required" with a secure link
5. Agent sends the secure link to owner (for SSN entry and payment)
6. Owner completes SSN entry and payment (approximately 2 minutes)
7. Webhook fires with status update — agent resumes
8. SFP files with the state, applies for EIN, delivers documents
9. Final webhook: status = "active"

## Human Actions Required

| Action             | What the Owner Does       | Time Required |
|--------------------|---------------------------|---------------|
| SSN/ITIN entry     | Enter SSN in secure form  | 30 seconds    |
| Payment approval   | Approve payment           | 30 seconds    |
| KYC (banking only) | Photo ID + selfie         | 2-3 minutes   |

## Status Codes

intake -> name_check -> name_reserved -> docs_generated ->
human_action_required -> ssn_collected -> payment_pending ->
payment_complete -> filed -> confirmed ->
ein_submitted -> ein_processing -> ein_issued -> active

Terminal: rejected, cancelled, dissolved
Error: filing_failed, ein_failed (with retry)

## Agent Authority

Entities are formed with an Agent Authority Schedule — an exhibit to the
operating agreement that defines the scope of actions the AI agent may take
on behalf of the LLC (e.g., accept payments, issue invoices, execute
contracts up to a defined limit). The human member is always the legal owner.

## Important Notes

- The human owner is the legal member. The agent operates under delegated authority.
- SSN/ITIN is encrypted (AES-256) and stored in a separate PII vault.
- SSN is never exposed to the agent or any LLM.
- This service forms standard LLCs — it does not create "AI-owned" entities.
- This is not legal advice. Templates are attorney-drafted but standardized.
"""


@router.get(
    "/llms.txt",
    response_class=PlainTextResponse,
    summary="LLMs.txt — machine-readable API description",
    description=(
        "Returns a plain-text description of the SFP Entity Formation API "
        "for AI agents and LLMs. Follows the llms.txt convention."
    ),
)
async def llms_txt() -> PlainTextResponse:
    return PlainTextResponse(content=LLMS_TXT_CONTENT, media_type="text/plain")
