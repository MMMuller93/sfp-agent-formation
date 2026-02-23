# Filing Automation Plan — State Entity Formation

## Overview

Automate the navigation and filing process for entity formation across state websites. Start with Delaware (primary), then expand to Wyoming and other jurisdictions. Uses Playwright for browser automation with human-in-the-loop for CAPTCHAs and payment.

## Current Assets

### Browser Recordings (Chrome DevTools Recorder format)
- `recordings/delaware/de-name-search-and-filing.puppeteer.js` — Puppeteer script (auto-exported)
- `recordings/delaware/de-name-search-and-filing.recording.json` — Raw recording JSON (re-playable)

### What the DE Recording Captures
1. Navigate to `https://corp.delaware.gov/`
2. Click "Name Availability Search" (corpServices3)
3. Accept disclaimer checkbox
4. Select entity type dropdown (Corporation / LLC / LP / etc.)
5. Select entity ending dropdown (L.L.C. / INC. / LP / etc.)
6. Enter entity name in search field
7. Solve CAPTCHA (image + audio fallback)
8. Click "Search" → navigates to results
9. Results page: "No, Perform New search" for retry
10. Navigate to "How to Form" page
11. Navigate to "Document Filing and Certificate Request Service"
12. Arrive at filing portal: `https://icis.corp.delaware.gov/ecorp2/`

---

## Delaware Division of Corporations — Site Map

### Key URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Home | `https://corp.delaware.gov/` | Main portal |
| Name Search | `https://icis.corp.delaware.gov/Ecorp/NameReserv/NameReservation.aspx` | Check name availability |
| Name Reservation | Same URL, post-search flow | Reserve available name (120 days, $75) |
| How to Form | `https://corp.delaware.gov/howtoform/` | Instructions for formation |
| Document Filing Info | `https://corp.delaware.gov/document-upload-service-information/` | Filing service overview |
| Filing Portal (eCorp2) | `https://icis.corp.delaware.gov/ecorp2/` | Actual document submission |
| Entity Search | `https://icis.corp.delaware.gov/Ecorp/EntitySearch/NameSearch.aspx` | Search existing entities |

### Name Search Form Elements

| Element | Selector | Type | Notes |
|---------|----------|------|-------|
| Disclaimer checkbox | `#ctl00_ContentPlaceHolder1_frmDisclaimerChkBox` | checkbox | Must check first |
| Entity Type | `#ctl00_ContentPlaceHolder1_frmEntityType` | select | CORPORATION, LLC, LP, etc. |
| Entity Ending | `#ctl00_ContentPlaceHolder1_frmEntityEnding` | select | INC., L.L.C., LP, etc. |
| Entity Name | `#ctl00_ContentPlaceHolder1_frmEntityName` | text | Case-insensitive |
| CAPTCHA Input | `#ctl00_ContentPlaceHolder1_ecorpCaptcha1_txtCaptcha` | text | Image CAPTCHA |
| CAPTCHA Refresh | `#btnRefresh` | button | Regenerate CAPTCHA |
| CAPTCHA Audio | `#playCaptchaButton` | button | Audio fallback |
| Search Button | `#ctl00_ContentPlaceHolder1_btnSubmit` | button | Submits form |

### Post-Search Elements

| Element | Selector | Purpose |
|---------|----------|---------|
| New Search | `#ctl00_ContentPlaceHolder1_btnNo` | "No, Perform New search" |

### Entity Type Options (DE)

| Value | Entity |
|-------|--------|
| `C` | Corporation |
| `Y` | Limited Liability Company (LLC) |
| `P` | Limited Partnership (LP) |
| `G` | General Partnership |
| `S` | Statutory Trust |

### Entity Ending Options (DE LLC)

| Value | Ending |
|-------|--------|
| `L.L.C.` | L.L.C. |
| `LLC` | LLC |
| `Limited Liability Company` | Limited Liability Company |

---

## Automation Architecture

### Approach: Playwright + Human Kernel for CAPTCHAs

```
Agent triggers name check
    ↓
Playwright navigates to DE name search
    ↓
Fills form (entity type, ending, name)
    ↓
[CAPTCHA GATE] → Two strategies:
    ├─ Strategy A: Audio CAPTCHA → Speech-to-text → auto-fill
    ├─ Strategy B: Screenshot CAPTCHA → human kernel webhook → human solves
    └─ Strategy C: Use registered agent API (Northwest, etc.) — bypasses state site
    ↓
Submit → Parse results
    ↓
Return availability status to agent
```

### CAPTCHA Strategy Decision

| Strategy | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| A: Audio STT | Fully automated | Fragile, may violate TOS, accuracy issues | V2 |
| B: Human solve | Reliable, TOS-safe | Adds latency (~30s) | MVP for manual filings |
| C: RA API | Best — no CAPTCHA | Cost, dependency on RA | MVP for name check |

**MVP recommendation**: Use **Strategy C** for name checks (registered agent APIs like Northwest, CSC, or Incfile often provide name search APIs). Fall back to **Strategy B** for direct state interaction when needed.

### Filing Portal Automation (eCorp2)

The eCorp2 filing portal (`https://icis.corp.delaware.gov/ecorp2/`) handles:
- Certificate of Formation filing
- Document uploads
- Payment processing

**Current status**: The recording shows the user navigated to ecorp2 but didn't go through the filing flow (noted as "down" at time of recording). This needs a separate recording session when the portal is available.

**Filing flow mapping needed**:
1. Account creation/login on eCorp2
2. Select filing type (Certificate of Formation - LLC)
3. Upload Certificate of Formation document
4. Payment ($90 base + any expedite fees)
5. Confirmation/receipt capture

---

## Submissions Tracking Database

### Schema Addition to EntityOrder

```python
# Add to existing FilingEvent model
class FilingEvent:
    # ... existing fields ...

    # Filing automation fields
    filing_channel: str  # "manual" | "playwright" | "ra_api" | "mail"
    state_confirmation_number: str  # DE file number
    state_filing_date: datetime
    state_filing_url: str  # Link to state filing receipt
    expedite_level: str  # "standard" | "24hr" | "same_day" | "2hr"
    filing_fee_paid: Decimal

    # For tracking submission attempts
    attempt_number: int
    automation_log: dict  # JSONB — screenshots, form data, errors
    captcha_method: str  # "audio_stt" | "human_solve" | "ra_api" | "n/a"
```

### Submissions History View (Ops Console)

```
GET /v1/admin/filings                → List all filing submissions
GET /v1/admin/filings/{id}/log       → Detailed automation log for a filing
GET /v1/admin/filings/stats          → Stats: success rate, avg time, by jurisdiction
```

---

## Filing Website Mapping — Expansion Plan

### Priority Jurisdictions

| # | State | Entity | Portal | CAPTCHA? | API Available? | Priority |
|---|-------|--------|--------|----------|----------------|----------|
| 1 | **Delaware** | LLC | eCorp2 | Yes (image) | Via RA | P0 — MVP |
| 2 | **Wyoming** | DAO LLC | WY SOS | Yes (reCAPTCHA) | No | P0 — MVP |
| 3 | Nevada | LLC | NV SilverFlume | No (account-based) | Partial | P1 |
| 4 | Florida | LLC | Sunbiz.org | No (account-based) | No | P2 |
| 5 | Texas | LLC | SOSDirect | No (account-based) | No | P2 |

### Per-Jurisdiction Mapping Template

For each new jurisdiction, create:

```
filing-automation/
  recordings/{state}/
    {state}-name-search.recording.json     # Chrome Recorder JSON
    {state}-name-search.puppeteer.js       # Auto-exported Puppeteer
    {state}-filing-flow.recording.json     # Full filing flow
  site-maps/{state}.md                     # Form elements, URLs, flow
  scripts/{state}/
    name_check.py                          # Playwright name check script
    file_formation.py                      # Playwright filing script
    parse_results.py                       # Result page parser
```

### Mapping Process (for each new state)

1. **Record**: Use Chrome DevTools Recorder to capture:
   - Name availability search flow
   - Full formation filing flow (if online)
   - Any account creation required

2. **Document**: Create site-map.md with:
   - All URLs in the flow
   - Form element selectors (ID, aria, xpath)
   - Required field values and options
   - CAPTCHA type and strategy
   - Fee schedule and payment flow

3. **Script**: Convert recording to Playwright Python:
   - Parameterize entity name, type, ending
   - Add error handling and retry logic
   - Add screenshot capture at each step
   - Add result parsing

4. **Test**: Dry-run with test entity names

5. **Integrate**: Wire into the API:
   - `POST /v1/entity-orders/{id}/name-check` calls the script
   - `POST /v1/entity-orders/{id}/filings/state/submit` calls the filing script
   - Results stored in FilingEvent with full automation log

---

## Wyoming Filing Portal

### Key URLs (to map)

| Service | URL | Notes |
|---------|-----|-------|
| WY SOS Home | `https://sos.wyo.gov/` | Secretary of State |
| Business Center | `https://sos.wyo.gov/Business/` | Entity services |
| Online Filing | `https://wyobiz.wyo.gov/` | Filing portal |
| Name Search | `https://wyobiz.wyo.gov/Business/FilingSearch.aspx` | Name availability |

### WY DAO LLC Specifics
- Wyoming recognizes "decentralized autonomous organization" as LLC supplement
- Articles of Organization must include DAO designation
- Smart contract address may be included in filing
- Additional requirements per WY Stat. § 17-31-101 through 17-31-115

---

## Implementation Phases

### Phase A: Name Check Automation (ships with MVP)

**Scope**: Automated name availability checking for DE and WY.

1. Convert DE browser recording to Playwright Python script
2. Parameterize: entity_name, entity_type, entity_ending
3. Handle CAPTCHA via:
   - Primary: Registered agent API (if available)
   - Fallback: Screenshot → human kernel → solve
4. Parse result page for availability status
5. Wire into `POST /v1/entity-orders/{id}/name-check` endpoint
6. Record WY name search flow + convert

### Phase B: Filing Submission Tracking (ships with MVP)

**Scope**: Manual filing with structured tracking.

1. Ops console filing queue (from state machine `docs_generated` → `state_filing_submitted`)
2. Ops manually files via state portal
3. Logs: confirmation number, date, fee, receipt screenshot
4. Updates order state → `state_confirmed`

### Phase C: Semi-Automated Filing (V2)

**Scope**: Playwright-assisted filing with human oversight.

1. Playwright fills forms up to payment
2. Human reviews pre-filled form
3. Human completes payment
4. Automation captures confirmation
5. Full automation log stored

### Phase D: Fully Automated Filing (V3)

**Scope**: End-to-end automated filing (where legally permitted).

1. Registered agent API for filing (CSC, Northwest)
2. Programmatic payment via saved payment method
3. Automatic receipt capture and parsing
4. No human involvement except monitoring

---

## Technical Notes

### Converting Recordings to Playwright Python

The Chrome Recorder exports Puppeteer JS. To convert to Playwright Python:

```python
# Pattern: Puppeteer → Playwright mapping
# puppeteer.Locator.race([...]) → page.locator("selector").click()
# targetPage.fill('value') → page.fill("selector", "value")
# targetPage.goto('url') → page.goto("url")
# targetPage.waitForNavigation() → page.wait_for_url("pattern")
```

Key differences:
- Playwright has better auto-wait (no explicit waitForNavigation needed)
- Use `page.locator()` with CSS/aria/text selectors
- `page.select_option()` for dropdowns instead of `fill()`
- Screenshots: `page.screenshot(path="path.png")`

### Anti-Detection Considerations

State websites may detect and block automated access:
- DE explicitly warns: "Use of automated tools in any form may result in suspension"
- Use realistic viewport sizes and timing delays
- Rotate user agents if needed
- Prefer API-based approaches (registered agent APIs) over scraping
- For direct automation: use it sparingly, add human-like delays
- Never mine data — only check specific names for actual filings

### CAPTCHA Solutions

| Method | Library/Service | Cost | Reliability |
|--------|----------------|------|-------------|
| Audio STT | OpenAI Whisper | ~$0.001/solve | Medium |
| Human-in-loop | Our human kernel | Free (human time) | High |
| CAPTCHA service | 2Captcha/Anti-Captcha | $1-3/1000 | High |
| RA API bypass | Northwest/CSC API | Included in RA fee | Highest |

**Recommendation**: RA API for production, human kernel for fallback.
