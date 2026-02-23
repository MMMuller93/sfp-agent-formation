# SFP Agent Entity Formation

AI-agent-native legal entity formation service. Agents (via MCP or API) can form LLCs, DAOs, corps, and trusts across US jurisdictions.

## Tech Stack

- **Backend**: Python 3.12 / FastAPI / SQLAlchemy (async) / Alembic / Pydantic v2
- **Frontend**: React 19 / Vite 6 / Tailwind v4 / TanStack Query / TypeScript
- **Database**: PostgreSQL (asyncpg) — two databases: main app + PII vault
- **Deployment**: Railway (API and frontend). No Vercel.
- **MCP Server**: Python, uses `mcp` SDK with `FastMCP`
- **Filing Automation**: Playwright (Python), Chrome DevTools Recorder exports in `filing-automation/`

## Project Layout

```
backend/         Python FastAPI application
frontend/        React/Vite SPA
shared/          OpenAPI spec and shared TS types
mcp-server/      MCP tool server for AI agent access
filing-automation/  Playwright scripts and state portal recordings
templates/       .docx formation document templates (docxtpl/Jinja2)
```

## Key Conventions

### PII Vault — Physical Isolation

Never store raw SSN, ITIN, passport numbers, or driver's license numbers in the main database. All PII goes to the vault database. The main DB stores only opaque `vault_ref` strings. This is enforced at the application layer; there are no cross-database joins.

### State Machine

Entity orders follow a strict state machine. All transitions must go through `VALID_TRANSITIONS` — never skip states or set state directly.

```
draft → pending_payment → payment_received → compliance_review
  → compliance_cleared → pii_collected → docs_generated
  → docs_approved → state_filing_submitted → state_confirmed → completed
```

Side transitions: `compliance_review → compliance_flagged`, any state → `cancelled`, `compliance_flagged → rejected`.

### Document Templates

Templates use `docxtpl` with Jinja2 strict mode (`jinja2.StrictUndefined`). Always validate all template variables are present before rendering — missing variables must raise, not silently produce blank fields.

### API Keys

API keys are SHA-256 hashed before storage. Never store plaintext API keys. The raw key is shown to the user exactly once at creation time.

### OpenAPI Contract Lock

After changing any FastAPI schema (request/response models, routes), regenerate the shared OpenAPI spec and frontend types:

```bash
# From backend: export the OpenAPI JSON
python -c "from app.main import app; import json; print(json.dumps(app.openapi()))" > ../shared/openapi.json

# From frontend: regenerate TS types
npm run generate:types
```

### Configuration

Backend config uses `pydantic-settings` with `SFP_` env prefix. See `backend/app/config.py`. A `.env` file in `backend/` is loaded automatically in development.

## Commands

### Backend

```bash
cd backend
pip install -r requirements.txt        # Install deps
pip install -e ".[dev]"                 # Install with dev tools
uvicorn app.main:app --reload          # Run dev server (port 8000)
pytest                                  # Run tests
ruff check .                           # Lint
ruff format .                          # Auto-format
alembic upgrade head                   # Run migrations
```

### Frontend

```bash
cd frontend
npm install                            # Install deps
npm run dev                            # Vite dev server (port 3000, proxies /v1 to backend)
npm run build                          # Production build (tsc + vite)
npx tsc --noEmit                       # Type check only
npm run generate:types                 # Regenerate API types from OpenAPI spec
```

### MCP Server

```bash
cd mcp-server
pip install -e .                       # Install
python server.py                       # Run MCP server
```

## Filing Automation

Scripts in `filing-automation/` automate state portal interactions (name checks, filings). Delaware recordings are in Puppeteer format (Chrome DevTools Recorder export), converted to Playwright Python in `scripts/`.

CAPTCHA handling strategy: prefer registered-agent API where available, fall back to human kernel (screenshot + webhook for human solving).

## Rules

- No Vercel. Railway for all deployments.
- No raw PII in main DB. Ever.
- State transitions go through `VALID_TRANSITIONS`. No exceptions.
- Template rendering uses `StrictUndefined`. No silent blanks.
- Regenerate OpenAPI spec + TS types after schema changes.
- API keys: SHA-256 hash only. No plaintext storage.
- Backend tests: `cd backend && pytest`
- Frontend build check: `cd frontend && npm run build`
