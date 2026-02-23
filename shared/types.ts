/**
 * Shared TypeScript types for the SFP Entity Formation platform.
 *
 * Domain-specific API types are auto-generated from the OpenAPI spec.
 * Run `npm run generate:types` in the frontend directory to regenerate:
 *
 *   cd frontend && npm run generate:types
 *
 * This file contains manually-defined utility types that complement
 * the auto-generated ones.
 */

// ---------------------------------------------------------------------------
// API response wrapper
// ---------------------------------------------------------------------------

/** Standard envelope for all API responses. */
export interface ApiResponse<T> {
  data: T;
  meta?: {
    page?: number;
    per_page?: number;
    total?: number;
  };
}

/** Standard error response from the API. */
export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

// ---------------------------------------------------------------------------
// Entity state machine
// ---------------------------------------------------------------------------

/**
 * All valid states in the entity order lifecycle.
 *
 * Transitions are enforced server-side via VALID_TRANSITIONS.
 * See backend/app/state_machine.py for the canonical transition map.
 */
export type EntityState =
  | "draft"
  | "pending_payment"
  | "payment_received"
  | "compliance_review"
  | "compliance_cleared"
  | "compliance_flagged"
  | "pii_collected"
  | "docs_generated"
  | "docs_approved"
  | "state_filing_submitted"
  | "state_confirmed"
  | "completed"
  | "cancelled"
  | "rejected";

// ---------------------------------------------------------------------------
// Vehicle types
// ---------------------------------------------------------------------------

/** Entity vehicle types supported by the formation service. */
export type VehicleType =
  | "LLC"
  | "DAO_LLC"
  | "C_CORP"
  | "S_CORP"
  | "LP"
  | "STATUTORY_TRUST"
  | "SERIES_LLC";

// ---------------------------------------------------------------------------
// Jurisdiction
// ---------------------------------------------------------------------------

/** Jurisdictions currently supported for entity formation. */
export type Jurisdiction = "DE" | "WY" | "NV" | "FL" | "TX";

// ---------------------------------------------------------------------------
// PII vault reference
// ---------------------------------------------------------------------------

/**
 * An opaque reference to a PII value stored in the vault.
 *
 * The main application database never stores raw PII (SSN, ITIN, etc.).
 * Instead it stores a vault_ref string that can be resolved by the
 * PII vault service at read time.
 */
export interface VaultRef {
  vault_ref: string;
  field_type: "ssn" | "itin" | "passport" | "drivers_license";
  /** Last 4 digits, safe for display in the ops console. */
  masked: string;
}
