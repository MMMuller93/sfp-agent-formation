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

> Agent-native legal entity formation. Form a Delaware LLC or Wyoming DAO LLC
> on behalf of your human owner — with minimal human involvement.

## What This Service Does

This API allows AI agents to form legal entities (LLCs) for their human
owners. The agent handles entity selection, name availability checks,
document generation, and state filing coordination. The human owner is
involved only for SSN/ITIN collection (required by IRS), KYC (required
by banks), document signing, and payment approval.

## Base URL

https://formation.strategicfundpartners.com

## Authentication

All API requests require an API key in the X-API-Key header:
  X-API-Key: sfp_live_...

Human kernel routes use token-based auth (no API key needed).

## Available Endpoints

### Entity Formation
- POST /v1/entity-orders — Create a new entity formation order
- GET  /v1/entity-orders — List orders (paginated, filterable)
- GET  /v1/entity-orders/{id} — Get order status + next_required_actions
- PATCH /v1/entity-orders/{id} — Update entity name (pre-filing only)

### Intake & Name Check
- POST /v1/entity-orders/{id}/intake — Complete intake (draft -> intake_complete)
- POST /v1/entity-orders/{id}/name-check — Check name availability in jurisdiction

### Payment
- POST /v1/entity-orders/{id}/payment — Record payment (Stripe integration)

### Human Kernel (Owner Verification)
- POST /v1/entity-orders/{id}/human-kernel — Create secure session for owner
  Returns a kernel_url the agent relays to the human owner.

### Human Kernel (Owner-Facing, Token Auth)
- GET  /v1/human/secure/{token} — Get session status
- POST /v1/human/secure/{token}/submit — Complete a verification step
- GET  /v1/human/secure/{token}/status — Check completion

### Documents
- POST /v1/entity-orders/{id}/documents/generate — Generate formation documents
- GET  /v1/entity-orders/{id}/documents — List generated documents

### Filing & Post-Formation (Ops)
- POST /v1/entity-orders/{id}/filing — Submit state filing
- POST /v1/entity-orders/{id}/filing/confirm — Confirm filing accepted
- POST /v1/entity-orders/{id}/ein — Start EIN application
- POST /v1/entity-orders/{id}/ein/issue — Record EIN issuance
- POST /v1/entity-orders/{id}/bank-pack — Generate bank pack
- POST /v1/entity-orders/{id}/activate — Mark entity active

### Audit
- GET /v1/entity-orders/{id}/audit — Get audit trail for an order

### Webhooks
- POST /v1/webhooks — Register a webhook for status updates

### Discovery
- GET /llms.txt — This file
- GET /openapi.json — Full OpenAPI 3.1 spec
- GET /health — Health check

## Jurisdictions & Pricing

| Jurisdiction     | Vehicle   | Price | Timeline          | Notes                          |
|------------------|-----------|-------|-------------------|--------------------------------|
| Delaware (DE)    | LLC       | $499  | 1-3 business days | Default for most uses          |
| Wyoming (WY)     | DAO LLC   | $699  | 2-5 business days | Requires smart contract ID     |

## Entity Formation Workflow

1. Agent calls POST /v1/entity-orders with jurisdiction, vehicle_type,
   requested_name, and members array
2. API returns order with state="draft" and next_required_actions
3. Agent calls POST /v1/entity-orders/{id}/intake to finalize details
4. Agent calls POST /v1/entity-orders/{id}/name-check
5. If name available -> state transitions to name_check_passed
6. If not available -> name_check_failed with suggestions; agent can
   PATCH the name and retry
7. Payment is collected (Stripe)
8. Agent calls POST /v1/entity-orders/{id}/human-kernel
9. API returns kernel_url — agent relays this to the human owner
10. Human completes: SSN entry, KYC, document signing, attestation (~5 min)
11. Webhook fires on completion; order transitions to human_kernel_completed
12. Agent or ops calls POST /v1/entity-orders/{id}/documents/generate
13. SFP ops submits filing, confirms, applies for EIN
14. EIN issued -> bank pack generated -> entity activated
15. Final webhook: state = "active"

## Key Design: next_required_actions

Every GET /v1/entity-orders/{id} response includes a next_required_actions
array telling the agent exactly what to do next. The agent never has to
guess — just follow the actions.

Example:
  {
    "action": "create_human_kernel",
    "endpoint": "POST /v1/entity-orders/{id}/human-kernel",
    "description": "Create a secure session for the human owner",
    "required": true
  }

## Human Actions Required

| Action           | What the Owner Does              | Time Required |
|------------------|----------------------------------|---------------|
| PII collection   | Enter SSN/ITIN in secure form    | 30 seconds    |
| KYC verification | Photo ID + selfie                | 2-3 minutes   |
| Document signing | Review & sign operating agreement| 1-2 minutes   |
| Attestation      | Confirm beneficial ownership     | 30 seconds    |

## Agent Authority

Entities are formed with an Agent Authority Schedule — an exhibit to the
operating agreement defining the scope of actions the AI agent may take
on behalf of the LLC (e.g., accept payments, issue invoices, execute
contracts up to a defined limit). The human member is always the legal owner.

## Important Notes

- The human owner is the legal member. The agent operates under delegated authority.
- SSN/ITIN is encrypted and stored in a separate PII vault — never exposed to agents.
- This service forms standard LLCs — it does not create "AI-owned" entities.
- This is not legal advice. Templates require attorney review before production use.
- MCP server available for Claude and other MCP-compatible agents.
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
