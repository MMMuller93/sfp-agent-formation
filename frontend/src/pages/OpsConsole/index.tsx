import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  XCircle,
  Activity,
  FileText,
  Send,
  CreditCard,
  Landmark,
  Zap,
  Filter,
  Building2,
} from "lucide-react";
import {
  api,
  type OrderSummary,
  type OrderState,
} from "@/lib/api";

// ---------- State display config ----------

interface StateDisplay {
  label: string;
  color: string;
  bg: string;
  border: string;
}

const STATE_DISPLAY: Partial<Record<OrderState, StateDisplay>> = {
  draft: {
    label: "Draft",
    color: "text-stone-400",
    bg: "bg-stone-400/10",
    border: "border-stone-700/40",
  },
  intake_complete: {
    label: "Intake Complete",
    color: "text-blue-400",
    bg: "bg-blue-400/10",
    border: "border-blue-700/40",
  },
  name_check_passed: {
    label: "Name Checked",
    color: "text-blue-400",
    bg: "bg-blue-400/10",
    border: "border-blue-700/40",
  },
  name_check_failed: {
    label: "Name Conflict",
    color: "text-orange-400",
    bg: "bg-orange-400/10",
    border: "border-orange-700/40",
  },
  payment_pending: {
    label: "Payment Pending",
    color: "text-yellow-400",
    bg: "bg-yellow-400/10",
    border: "border-yellow-700/40",
  },
  payment_complete: {
    label: "Paid",
    color: "text-green-400",
    bg: "bg-green-400/10",
    border: "border-green-700/40",
  },
  human_kernel_required: {
    label: "KYC Required",
    color: "text-yellow-400",
    bg: "bg-yellow-400/10",
    border: "border-yellow-700/40",
  },
  human_kernel_completed: {
    label: "KYC Done",
    color: "text-green-400",
    bg: "bg-green-400/10",
    border: "border-green-700/40",
  },
  docs_generated: {
    label: "Docs Ready",
    color: "text-blue-400",
    bg: "bg-blue-400/10",
    border: "border-blue-700/40",
  },
  state_filing_submitted: {
    label: "Filing Submitted",
    color: "text-yellow-400",
    bg: "bg-yellow-400/10",
    border: "border-yellow-700/40",
  },
  state_confirmed: {
    label: "State Confirmed",
    color: "text-green-400",
    bg: "bg-green-400/10",
    border: "border-green-700/40",
  },
  ein_pending: {
    label: "EIN Pending",
    color: "text-yellow-400",
    bg: "bg-yellow-400/10",
    border: "border-yellow-700/40",
  },
  ein_issued: {
    label: "EIN Issued",
    color: "text-green-400",
    bg: "bg-green-400/10",
    border: "border-green-700/40",
  },
  bank_pack_ready: {
    label: "Bank Pack Ready",
    color: "text-blue-400",
    bg: "bg-blue-400/10",
    border: "border-blue-700/40",
  },
  active: {
    label: "Active",
    color: "text-emerald-400",
    bg: "bg-emerald-400/10",
    border: "border-emerald-700/40",
  },
  failed: {
    label: "Failed",
    color: "text-red-400",
    bg: "bg-red-400/10",
    border: "border-red-700/40",
  },
  cancelled: {
    label: "Cancelled",
    color: "text-stone-500",
    bg: "bg-stone-500/10",
    border: "border-stone-700/40",
  },
};

const DEFAULT_DISPLAY: StateDisplay = {
  label: "Unknown",
  color: "text-stone-500",
  bg: "bg-stone-500/10",
  border: "border-stone-700/40",
};

function getStateDisplay(state: OrderState): StateDisplay {
  return STATE_DISPLAY[state] ?? DEFAULT_DISPLAY;
}

// ---------- Action config ----------

interface OrderAction {
  label: string;
  icon: typeof Send;
  handler: (orderId: string) => Promise<unknown>;
  confirmLabel?: string;
}

const STATE_ACTIONS: Partial<Record<OrderState, OrderAction>> = {
  docs_generated: {
    label: "Submit Filing",
    icon: Send,
    handler: (id) => api.orders.submitFiling(id),
    confirmLabel: "Submit state filing?",
  },
  state_filing_submitted: {
    label: "Confirm Filing",
    icon: CheckCircle2,
    // Confirm filing = name-check step to advance state
    handler: (id) => api.orders.nameCheck(id),
    confirmLabel: "Confirm state filing was accepted?",
  },
  state_confirmed: {
    label: "Start EIN",
    icon: FileText,
    handler: (id) => api.orders.startEin(id),
    confirmLabel: "Start IRS EIN application?",
  },
  ein_pending: {
    label: "Issue EIN",
    icon: CreditCard,
    // Mark EIN as issued = generate bank pack triggers transition
    handler: (id) => api.orders.generateBankPack(id),
    confirmLabel: "Mark EIN as issued?",
  },
  ein_issued: {
    label: "Generate Bank Pack",
    icon: Landmark,
    handler: (id) => api.orders.generateBankPack(id),
    confirmLabel: "Generate bank pack?",
  },
  bank_pack_ready: {
    label: "Activate",
    icon: Zap,
    handler: (id) => api.orders.activate(id),
    confirmLabel: "Activate entity and mark fully formed?",
  },
};

// ---------- Stats computation ----------

type StatCategory = "pending" | "in_progress" | "completed" | "failed";

function categorise(state: OrderState): StatCategory {
  if (state === "active") return "completed";
  if (state === "failed" || state === "cancelled") return "failed";
  if (state === "draft" || state === "payment_pending") return "pending";
  return "in_progress";
}

interface Stats {
  pending: number;
  in_progress: number;
  completed: number;
  failed: number;
}

function computeStats(orders: OrderSummary[]): Stats {
  const stats: Stats = { pending: 0, in_progress: 0, completed: 0, failed: 0 };
  for (const o of orders) {
    stats[categorise(o.state)]++;
  }
  return stats;
}

// ---------- Filters ----------

const ALL_STATES: OrderState[] = [
  "draft",
  "intake_complete",
  "name_check_passed",
  "name_check_failed",
  "payment_pending",
  "payment_complete",
  "human_kernel_required",
  "human_kernel_completed",
  "docs_generated",
  "state_filing_submitted",
  "state_confirmed",
  "ein_pending",
  "ein_issued",
  "bank_pack_ready",
  "active",
  "failed",
  "cancelled",
];

// ---------- Components ----------

function StatCard({
  label,
  value,
  color,
  icon: Icon,
  index,
}: {
  label: string;
  value: number;
  color: string;
  icon: typeof Activity;
  index: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: index * 0.05, ease: "easeOut" }}
      className="rounded-xl border border-stone-800/60 bg-stone-900/40 p-5"
    >
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-widest text-stone-500">
          {label}
        </p>
        <Icon className={`h-4 w-4 ${color}`} strokeWidth={1.5} />
      </div>
      <p className={`mt-3 text-3xl font-semibold tabular-nums ${color}`}>
        {value}
      </p>
    </motion.div>
  );
}

function StateBadge({ state }: { state: OrderState }) {
  const d = getStateDisplay(state);
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${d.color} ${d.bg} ${d.border}`}
    >
      {d.label}
    </span>
  );
}

function ActionButton({
  orderId,
  state,
  onSuccess,
}: {
  orderId: string;
  state: OrderState;
  onSuccess: () => void;
}) {
  const action = STATE_ACTIONS[state];
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  if (!action) return null;

  // Capture narrowed reference for use inside async closure.
  const resolvedAction = action;
  const Icon = resolvedAction.icon;

  async function handleClick() {
    const confirmed = resolvedAction.confirmLabel
      ? window.confirm(resolvedAction.confirmLabel)
      : true;
    if (!confirmed) return;

    setBusy(true);
    setErr(null);
    try {
      await resolvedAction.handler(orderId);
      onSuccess();
    } catch (e: unknown) {
      const detail =
        e !== null &&
        typeof e === "object" &&
        "detail" in e &&
        typeof (e as { detail: unknown }).detail === "string"
          ? (e as { detail: string }).detail
          : "Action failed";
      setErr(detail);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={() => void handleClick()}
        disabled={busy}
        className="inline-flex items-center gap-1.5 rounded-md border border-bronze-500/40 bg-bronze-500/10 px-3 py-1.5 text-xs font-semibold text-bronze-300 transition-all duration-150 hover:border-bronze-400/60 hover:bg-bronze-500/20 hover:text-bronze-200 disabled:cursor-not-allowed disabled:opacity-40"
      >
        {busy ? (
          <RefreshCw className="h-3 w-3 animate-spin" />
        ) : (
          <Icon className="h-3 w-3" strokeWidth={1.5} />
        )}
        {busy ? "Working…" : action.label}
      </button>
      {err && (
        <p className="max-w-[180px] text-right text-[10px] leading-tight text-red-400">
          {err}
        </p>
      )}
    </div>
  );
}

function SkeletonRow() {
  return (
    <tr className="animate-pulse border-b border-stone-800/40">
      {Array.from({ length: 6 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 rounded bg-stone-800/60" />
        </td>
      ))}
    </tr>
  );
}

// ---------- Audit log tab (stub) ----------

interface AuditEvent {
  id: string;
  timestamp: string;
  order_id: string;
  event: string;
  detail: string;
}

function AuditLog() {
  // Audit events are not yet exposed by the API; show a placeholder.
  const MOCK_EVENTS: AuditEvent[] = [
    {
      id: "1",
      timestamp: new Date(Date.now() - 120000).toISOString(),
      order_id: "a1b2c3d4",
      event: "state.changed",
      detail: "docs_generated → state_filing_submitted",
    },
    {
      id: "2",
      timestamp: new Date(Date.now() - 300000).toISOString(),
      order_id: "e5f6g7h8",
      event: "state.changed",
      detail: "state_confirmed → ein_pending",
    },
    {
      id: "3",
      timestamp: new Date(Date.now() - 600000).toISOString(),
      order_id: "i9j0k1l2",
      event: "order.created",
      detail: 'New order "Meridian Holdings LLC" (DE/LLC)',
    },
  ];

  return (
    <div className="rounded-xl border border-stone-800/60 bg-stone-900/40">
      <div className="border-b border-stone-800/60 px-6 py-4">
        <h2 className="text-sm font-semibold text-stone-200">
          Recent Audit Events
        </h2>
        <p className="mt-0.5 text-xs text-stone-500">
          Live audit stream not yet connected — showing mock data.
        </p>
      </div>
      <div className="divide-y divide-stone-800/40">
        {MOCK_EVENTS.map((ev) => (
          <div key={ev.id} className="flex items-start gap-4 px-6 py-4">
            <div className="mt-0.5 flex-shrink-0">
              <Activity
                className="h-4 w-4 text-bronze-500/60"
                strokeWidth={1.5}
              />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-stone-300">
                  {ev.event}
                </span>
                <span className="rounded bg-stone-800/60 px-1.5 py-0.5 font-mono text-[10px] text-stone-500">
                  {ev.order_id}
                </span>
              </div>
              <p className="mt-0.5 truncate text-xs text-stone-500">
                {ev.detail}
              </p>
            </div>
            <time className="flex-shrink-0 text-[10px] text-stone-600">
              {new Date(ev.timestamp).toLocaleTimeString("en-US", {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
              })}
            </time>
          </div>
        ))}
      </div>
    </div>
  );
}

// ---------- Main page ----------

type ActiveTab = "queue" | "audit";

export function OpsConsole() {
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<ActiveTab>("queue");

  // Filters
  const [filterState, setFilterState] = useState<string>("");
  const [filterJurisdiction, setFilterJurisdiction] = useState<string>("");

  const fetchOrders = useCallback(async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true);

    try {
      const params: { state?: string; jurisdiction?: string } = {};
      if (filterState) params.state = filterState;
      if (filterJurisdiction) params.jurisdiction = filterJurisdiction;

      const data = await api.orders.list(params);
      setOrders(data.orders);
      setError(null);
    } catch (err: unknown) {
      const message =
        err !== null &&
        typeof err === "object" &&
        "detail" in err &&
        typeof (err as { detail: unknown }).detail === "string"
          ? (err as { detail: string }).detail
          : "Failed to load orders.";
      setError(message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filterState, filterJurisdiction]);

  // Initial load and re-fetch when filters change
  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (cancelled) return;
      setLoading(true);
      await fetchOrders();
    }

    void load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterState, filterJurisdiction]);

  const stats = computeStats(orders);

  const handleActionSuccess = useCallback(() => {
    void fetchOrders(true);
  }, [fetchOrders]);

  return (
    <section className="relative">
      {/* Subtle background glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 70% 30% at 50% 0%, rgba(191,159,117,0.03) 0%, transparent 55%)",
        }}
      />

      <div className="relative mx-auto max-w-7xl px-6 py-14">
        {/* ── Header ────────────────────────────────── */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-bronze-500">
              Internal
            </p>
            <h1 className="heading-display mt-1.5 text-3xl text-stone-100">
              Ops Console
            </h1>
            <p className="mt-1 text-sm text-stone-500">
              Monitor and advance active entity formation orders.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void fetchOrders(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-lg border border-stone-700/60 bg-stone-900/60 px-4 py-2 text-sm text-stone-300 transition-all hover:border-stone-600 hover:text-stone-100 disabled:opacity-40"
          >
            <RefreshCw
              className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
              strokeWidth={1.5}
            />
            Refresh
          </button>
        </div>

        {/* ── Stats ─────────────────────────────────── */}
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard
            label="Pending"
            value={stats.pending}
            color="text-stone-400"
            icon={Clock}
            index={0}
          />
          <StatCard
            label="In Progress"
            value={stats.in_progress}
            color="text-blue-400"
            icon={Activity}
            index={1}
          />
          <StatCard
            label="Completed"
            value={stats.completed}
            color="text-emerald-400"
            icon={CheckCircle2}
            index={2}
          />
          <StatCard
            label="Failed"
            value={stats.failed}
            color="text-red-400"
            icon={XCircle}
            index={3}
          />
        </div>

        {/* ── Tabs ──────────────────────────────────── */}
        <div className="mt-8 flex items-center gap-1 border-b border-stone-800/60">
          {(["queue", "audit"] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2.5 text-sm font-medium transition-colors duration-150 ${
                activeTab === tab
                  ? "border-b-2 border-bronze-500 text-bronze-400"
                  : "text-stone-500 hover:text-stone-300"
              }`}
            >
              {tab === "queue" ? "Order Queue" : "Audit Log"}
            </button>
          ))}
        </div>

        {/* ── Tab content ───────────────────────────── */}
        <div className="mt-6">
          {activeTab === "queue" && (
            <QueueTab
              orders={orders}
              loading={loading}
              error={error}
              filterState={filterState}
              filterJurisdiction={filterJurisdiction}
              onFilterState={setFilterState}
              onFilterJurisdiction={setFilterJurisdiction}
              onActionSuccess={handleActionSuccess}
            />
          )}
          {activeTab === "audit" && <AuditLog />}
        </div>
      </div>
    </section>
  );
}

// ---------- Queue tab ----------

function QueueTab({
  orders,
  loading,
  error,
  filterState,
  filterJurisdiction,
  onFilterState,
  onFilterJurisdiction,
  onActionSuccess,
}: {
  orders: OrderSummary[];
  loading: boolean;
  error: string | null;
  filterState: string;
  filterJurisdiction: string;
  onFilterState: (v: string) => void;
  onFilterJurisdiction: (v: string) => void;
  onActionSuccess: () => void;
}) {
  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 rounded-lg border border-stone-800/60 bg-stone-900/40 px-3 py-2">
          <Filter className="h-3.5 w-3.5 text-stone-500" strokeWidth={1.5} />
          <span className="text-xs text-stone-500">Filter:</span>
        </div>

        {/* Status filter */}
        <select
          value={filterState}
          onChange={(e) => onFilterState(e.target.value)}
          className="rounded-lg border border-stone-800/60 bg-stone-900/60 px-3 py-2 text-xs text-stone-300 outline-none focus:border-bronze-500/40 focus:ring-1 focus:ring-bronze-500/20"
        >
          <option value="">All statuses</option>
          {ALL_STATES.map((s) => (
            <option key={s} value={s}>
              {getStateDisplay(s).label}
            </option>
          ))}
        </select>

        {/* Jurisdiction filter */}
        <select
          value={filterJurisdiction}
          onChange={(e) => onFilterJurisdiction(e.target.value)}
          className="rounded-lg border border-stone-800/60 bg-stone-900/60 px-3 py-2 text-xs text-stone-300 outline-none focus:border-bronze-500/40 focus:ring-1 focus:ring-bronze-500/20"
        >
          <option value="">All jurisdictions</option>
          <option value="DE">Delaware (DE)</option>
          <option value="WY">Wyoming (WY)</option>
        </select>

        {/* Clear filters */}
        {(filterState || filterJurisdiction) && (
          <button
            type="button"
            onClick={() => {
              onFilterState("");
              onFilterJurisdiction("");
            }}
            className="rounded-lg border border-stone-800/60 bg-stone-900/40 px-3 py-2 text-xs text-stone-500 transition-colors hover:text-stone-300"
          >
            Clear
          </button>
        )}

        {/* Result count */}
        <span className="ml-auto text-xs text-stone-600">
          {orders.length} order{orders.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Error banner */}
      {error && (
        <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3">
          <AlertTriangle className="h-4 w-4 shrink-0 text-red-400" strokeWidth={1.5} />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-stone-800/60">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-stone-800/60 bg-stone-900/60">
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-stone-500">
                ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-stone-500">
                Entity Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-stone-500">
                Jurisdiction
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-stone-500">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-stone-500">
                Created
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wider text-stone-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-stone-950/40 divide-y divide-stone-800/40">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
            ) : orders.length === 0 ? (
              <tr>
                <td
                  colSpan={6}
                  className="px-4 py-16 text-center"
                >
                  <div className="flex flex-col items-center gap-3">
                    <Building2
                      className="h-8 w-8 text-stone-700"
                      strokeWidth={1.5}
                    />
                    <p className="text-sm text-stone-500">
                      No orders match the current filters.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              orders.map((order, i) => (
                <OrderRow
                  key={order.id}
                  order={order}
                  index={i}
                  onActionSuccess={onActionSuccess}
                />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ---------- Order row ----------

function OrderRow({
  order,
  index,
  onActionSuccess,
}: {
  order: OrderSummary;
  index: number;
  onActionSuccess: () => void;
}) {
  // Short UUID: first 8 chars
  const shortId = order.id.replace(/-/g, "").slice(0, 8).toUpperCase();

  const createdDate = new Date(order.created_at).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <motion.tr
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.2, delay: Math.min(index * 0.03, 0.3) }}
      className="transition-colors hover:bg-stone-900/60"
    >
      {/* ID */}
      <td className="px-4 py-3">
        <span className="font-mono text-xs text-stone-500">{shortId}</span>
      </td>

      {/* Entity name */}
      <td className="px-4 py-3">
        <span className="font-medium text-stone-200">{order.requested_name}</span>
      </td>

      {/* Jurisdiction */}
      <td className="px-4 py-3">
        <span className="rounded bg-stone-800/60 px-2 py-0.5 text-xs font-medium text-stone-400">
          {order.jurisdiction}
        </span>
      </td>

      {/* Status */}
      <td className="px-4 py-3">
        <StateBadge state={order.state} />
      </td>

      {/* Created */}
      <td className="px-4 py-3">
        <span className="text-xs text-stone-500">{createdDate}</span>
      </td>

      {/* Actions */}
      <td className="px-4 py-3 text-right">
        <ActionButton
          orderId={order.id}
          state={order.state}
          onSuccess={onActionSuccess}
        />
      </td>
    </motion.tr>
  );
}
