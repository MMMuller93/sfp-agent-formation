import { config } from "@/config";

// ---------- Types ----------
// These will be replaced by generated OpenAPI types once the backend
// schema is available.  Run `npm run generate:types` to regenerate.

/** Placeholder entity order type until OpenAPI codegen is wired up. */
export interface EntityOrder {
  id: string;
  status: string;
  entity_name: string;
  jurisdiction: string;
  created_at: string;
}

export interface CreateOrderPayload {
  entity_name: string;
  jurisdiction: "DE" | "WY";
  agent_callback_url?: string;
  beneficial_owners: Array<{
    name: string;
    address: string;
    ownership_pct: number;
  }>;
}

export interface ApiError {
  detail: string;
  status: number;
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
 * API key header when available, and normalises errors.
 */
async function apiFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");

  if (_apiKey) {
    headers.set(API_KEY_HEADER, _apiKey);
  }

  const res = await fetch(`${config.apiBaseUrl}${path}`, {
    ...init,
    headers,
  });

  if (!res.ok) {
    const body = (await res.json().catch(() => ({
      detail: res.statusText,
    }))) as { detail?: string };

    const err: ApiError = {
      detail: body.detail ?? "Unknown API error",
      status: res.status,
    };
    throw err;
  }

  // 204 No Content
  if (res.status === 204) return undefined as T;

  return res.json() as Promise<T>;
}

// ---------- Typed endpoint helpers ----------

export const api = {
  orders: {
    list: () => apiFetch<EntityOrder[]>("/v1/orders"),
    get: (id: string) => apiFetch<EntityOrder>(`/v1/orders/${id}`),
    create: (payload: CreateOrderPayload) =>
      apiFetch<EntityOrder>("/v1/orders", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
  },
} as const;
