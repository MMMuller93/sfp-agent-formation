import { config } from "@/config";

// ---------- Core domain types ----------
// Derived from shared/openapi.json. Run `npm run generate:types` to regenerate.

export type OrderState =
  | "draft"
  | "intake_complete"
  | "name_check_passed"
  | "name_check_failed"
  | "payment_pending"
  | "payment_complete"
  | "human_kernel_required"
  | "human_kernel_completed"
  | "docs_generated"
  | "state_filing_submitted"
  | "state_confirmed"
  | "ein_pending"
  | "ein_issued"
  | "bank_pack_ready"
  | "active"
  | "failed"
  | "cancelled";

export type VehicleType = "llc" | "dao_llc" | "corporation";
export type ServiceTier = "self_serve" | "managed" | "autonomous";
export type MemberRole =
  | "member"
  | "manager"
  | "registered_agent"
  | "responsible_party";
export type KernelStep =
  | "pii_collection"
  | "kyc_verification"
  | "document_signing"
  | "attestation";

/** Describes a next action the caller should take to advance the order. */
export interface ActionItem {
  action: string;
  endpoint: string | null;
  description: string;
  required: boolean;
}

/** Full order representation returned by POST/GET /v1/entity-orders */
export interface OrderResponse {
  id: string;
  jurisdiction: string;
  vehicle_type: string;
  requested_name: string;
  formatted_name: string | null;
  state: OrderState;
  service_tier: string;
  pricing_cents: number;
  payment_status: string;
  next_required_actions: ActionItem[];
  created_at: string;
  updated_at: string | null;
}

/** Lightweight summary used in paginated list responses */
export interface OrderSummary {
  id: string;
  requested_name: string;
  state: OrderState;
  jurisdiction: string;
  vehicle_type: string;
  created_at: string;
}

/** Paginated list response for GET /v1/entity-orders */
export interface OrderListResponse {
  orders: OrderSummary[];
  total: number;
  page: number;
  per_page: number;
}

/** Returned after every successful state-transition action */
export interface StateTransitionResponse {
  previous_state: string;
  new_state: string;
  timestamp: string;
  order: OrderResponse;
}

/** Member input for order creation */
export interface MemberInput {
  legal_name: string;
  email?: string | null;
  role?: MemberRole;
  ownership_percentage?: number | null;
}

/** AI agent input for order creation */
export interface AgentInput {
  display_name: string;
  authority_scope: Record<string, unknown>;
  transaction_limit_cents?: number | null;
}

/** POST /v1/entity-orders request body */
export interface CreateOrderRequest {
  jurisdiction: string;
  vehicle_type: VehicleType;
  requested_name: string;
  service_tier?: ServiceTier;
  members: MemberInput[];
  agent?: AgentInput | null;
  metadata?: Record<string, unknown> | null;
}

/** Name check result from POST /v1/entity-orders/{id}/name-check */
export interface NameCheckResponse {
  available: boolean;
  jurisdiction: string;
  entity_name: string;
  message: string;
  method: string;
  suggestions: string[];
  transition: StateTransitionResponse | null;
}

/** Human kernel creation response */
export interface CreateKernelResponse {
  kernel_url: string;
  token_prefix: string;
  expires_at: string;
  suggested_message: string;
}

/** Document summary */
export interface DocumentSummary {
  id: string;
  doc_type: string;
  template_version: string;
  file_hash: string;
  signing_status: string;
  created_at: string;
}

/** Audit event */
export interface AuditEventItem {
  id: string;
  actor: string;
  action: string;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

/** PATCH /v1/entity-orders/{order_id} request body */
export interface UpdateNameRequest {
  requested_name: string;
}

/** Optional filters for GET /v1/entity-orders */
export interface ListOrdersParams {
  page?: number;
  per_page?: number;
  jurisdiction?: string;
  state?: string;
}

/** POST /v1/webhooks request body */
export interface CreateWebhookRequest {
  url: string;
  events: string[];
}

/** Webhook registration returned by POST /v1/webhooks */
export interface WebhookResponse {
  id: string;
  url: string;
  events: string[];
  active: boolean;
  created_at: string;
}

/** GET /v1/human/secure/{token} response */
export interface KernelSessionStatus {
  token_prefix: string;
  status: "pending" | "in_progress" | "completed" | "expired";
  completed_steps: string[];
  remaining_steps: string[];
  expires_at: string;
  is_expired: boolean;
}

/** POST /v1/human/secure/{token}/submit request body */
export interface StepSubmission {
  step: KernelStep;
  data?: Record<string, unknown>;
}

/** POST /v1/human/secure/{token}/submit response */
export interface StepResponse {
  step: string;
  status: string;
  completed_steps: string[];
  remaining_steps: string[];
  all_complete: boolean;
}

/** GET /health response */
export interface HealthResponse {
  status: string;
  version: string;
}

/** Normalised error thrown by apiFetch on non-2xx responses */
export class ApiError extends Error {
  detail: string;
  status: number;

  constructor(detail: string, status: number) {
    super(detail);
    this.name = "ApiError";
    this.detail = detail;
    this.status = status;
  }
}

/**
 * Legacy alias kept so Dashboard and OrderDetail pages compile without
 * changes. The api.orders.list() helper now returns OrderListResponse;
 * callers that rely on EntityOrder should migrate to OrderSummary.
 *
 * @deprecated Use OrderSummary or OrderResponse directly.
 */
export interface EntityOrder {
  id: string;
  /** @deprecated Use requested_name */
  entity_name: string;
  /** @deprecated Use state */
  status: string;
  jurisdiction: string;
  created_at: string;
}

// ---------- Fetch wrapper ----------

const API_KEY_HEADER = "X-API-Key";

let _apiKey: string | null = null;

/** Set the API key used for subsequent requests. */
export function setApiKey(key: string): void {
  _apiKey = key;
}

/** Clear the stored API key. */
export function clearApiKey(): void {
  _apiKey = null;
}

/**
 * Low-level fetch wrapper that prepends the API base URL, attaches the
 * API key header when available, and normalises non-2xx responses into
 * an ApiError object.
 */
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");

  if (_apiKey) {
    headers.set(API_KEY_HEADER, _apiKey);
  }

  const res = await fetch(`${config.apiBaseUrl}${path}`, { ...init, headers });

  if (!res.ok) {
    const body = (await res.json().catch(() => ({
      detail: res.statusText,
    }))) as { detail?: string };

    throw new ApiError(body.detail ?? "Unknown API error", res.status);
  }

  // 204 No Content — return undefined cast to T
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

/** Build a URL query string, omitting keys with undefined/null/"" values. */
function buildQuery(
  params: Record<string, string | number | undefined | null>,
): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== "",
  );
  if (entries.length === 0) return "";
  const qs = new URLSearchParams(entries.map(([k, v]) => [k, String(v)]));
  return `?${qs.toString()}`;
}

// ---------- Typed endpoint helpers ----------

export const api = {
  // ── Entity Orders ──────────────────────────────────────────────────────────

  orders: {
    /** POST /v1/entity-orders — create a new formation order */
    create: (payload: CreateOrderRequest) =>
      apiFetch<OrderResponse>("/v1/entity-orders", {
        method: "POST",
        body: JSON.stringify(payload),
      }),

    /** GET /v1/entity-orders — paginated list with optional filters */
    list: (params?: ListOrdersParams) =>
      apiFetch<OrderListResponse>(
        `/v1/entity-orders${buildQuery({
          page: params?.page,
          per_page: params?.per_page,
          jurisdiction: params?.jurisdiction,
          state: params?.state,
        })}`,
      ),

    /** GET /v1/entity-orders/{order_id} — fetch a single order by ID */
    get: (orderId: string) =>
      apiFetch<OrderResponse>(`/v1/entity-orders/${orderId}`),

    /** PATCH /v1/entity-orders/{order_id} — update the requested entity name */
    updateName: (orderId: string, payload: UpdateNameRequest) =>
      apiFetch<OrderResponse>(`/v1/entity-orders/${orderId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),

    /** POST /v1/entity-orders/{order_id}/intake — complete intake */
    completeIntake: (orderId: string) =>
      apiFetch<StateTransitionResponse>(
        `/v1/entity-orders/${orderId}/intake`,
        { method: "POST" },
      ),

    /** POST /v1/entity-orders/{order_id}/name-check — run name availability check */
    nameCheck: (orderId: string) =>
      apiFetch<NameCheckResponse>(
        `/v1/entity-orders/${orderId}/name-check`,
        { method: "POST" },
      ),

    /** POST /v1/entity-orders/{order_id}/payment — record payment */
    recordPayment: (orderId: string) =>
      apiFetch<StateTransitionResponse>(
        `/v1/entity-orders/${orderId}/payment`,
        { method: "POST" },
      ),

    /** POST /v1/entity-orders/{order_id}/human-kernel — create human kernel session */
    createKernel: (orderId: string) =>
      apiFetch<CreateKernelResponse>(
        `/v1/entity-orders/${orderId}/human-kernel`,
        { method: "POST" },
      ),

    /** POST /v1/entity-orders/{order_id}/documents/generate — generate formation documents */
    generateDocuments: (orderId: string) =>
      apiFetch<StateTransitionResponse>(
        `/v1/entity-orders/${orderId}/documents/generate`,
        { method: "POST" },
      ),

    /** GET /v1/entity-orders/{order_id}/documents — list generated documents */
    listDocuments: (orderId: string) =>
      apiFetch<DocumentSummary[]>(`/v1/entity-orders/${orderId}/documents`),

    /** POST /v1/entity-orders/{order_id}/filing — submit state filing */
    submitFiling: (orderId: string) =>
      apiFetch<StateTransitionResponse>(
        `/v1/entity-orders/${orderId}/filing`,
        { method: "POST" },
      ),

    /** POST /v1/entity-orders/{order_id}/filing/confirm — confirm state filing */
    confirmFiling: (orderId: string) =>
      apiFetch<StateTransitionResponse>(
        `/v1/entity-orders/${orderId}/filing/confirm`,
        { method: "POST" },
      ),

    /** POST /v1/entity-orders/{order_id}/ein — start EIN application (Form SS-4) */
    startEin: (orderId: string) =>
      apiFetch<StateTransitionResponse>(`/v1/entity-orders/${orderId}/ein`, {
        method: "POST",
      }),

    /** POST /v1/entity-orders/{order_id}/ein/issue — record EIN issuance */
    issueEin: (orderId: string) =>
      apiFetch<StateTransitionResponse>(
        `/v1/entity-orders/${orderId}/ein/issue`,
        { method: "POST" },
      ),

    /** POST /v1/entity-orders/{order_id}/bank-pack — generate bank pack document bundle */
    generateBankPack: (orderId: string) =>
      apiFetch<StateTransitionResponse>(
        `/v1/entity-orders/${orderId}/bank-pack`,
        { method: "POST" },
      ),

    /** POST /v1/entity-orders/{order_id}/activate — mark entity as fully active */
    activate: (orderId: string) =>
      apiFetch<StateTransitionResponse>(
        `/v1/entity-orders/${orderId}/activate`,
        { method: "POST" },
      ),

    /** GET /v1/entity-orders/{order_id}/audit — get audit trail */
    getAuditTrail: (orderId: string, limit?: number) =>
      apiFetch<AuditEventItem[]>(
        `/v1/entity-orders/${orderId}/audit${buildQuery({ limit })}`,
      ),
  },

  // ── Webhooks ────────────────────────────────────────────────────────────────

  webhooks: {
    /** POST /v1/webhooks — register a URL to receive status-change notifications */
    register: (payload: CreateWebhookRequest) =>
      apiFetch<WebhookResponse>("/v1/webhooks", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },

  // ── Human Kernel ────────────────────────────────────────────────────────────

  kernel: {
    /** GET /v1/human/secure/{token} — get kernel session status and pending steps */
    getSession: (token: string) =>
      apiFetch<KernelSessionStatus>(`/v1/human/secure/${token}`),

    /** GET /v1/human/secure/{token}/status — quick check whether human completed all steps */
    checkCompletion: (token: string) =>
      apiFetch<Record<string, unknown>>(`/v1/human/secure/${token}/status`),

    /** POST /v1/human/secure/{token}/submit — submit a completed kernel step */
    submitStep: (token: string, payload: StepSubmission) =>
      apiFetch<StepResponse>(`/v1/human/secure/${token}/submit`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },

  // ── Health ──────────────────────────────────────────────────────────────────

  health: {
    /** GET /health — service liveness check */
    check: () => apiFetch<HealthResponse>("/health"),
  },
} as const;
