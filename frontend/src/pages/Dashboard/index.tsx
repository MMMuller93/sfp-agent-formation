import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Building2,
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Plus,
  ArrowRight,
} from "lucide-react";
import { api, type EntityOrder } from "@/lib/api";

/* ─── State configuration ───────────────────────────────────── */

interface StateDisplay {
  color: string;
  icon: typeof Building2;
  label: string;
}

const STATE_CONFIG: Record<string, StateDisplay> = {
  draft: { color: "text-stone-400", icon: Clock, label: "Draft" },
  intake_complete: {
    color: "text-blue-400",
    icon: Building2,
    label: "Intake Complete",
  },
  name_check_passed: {
    color: "text-blue-400",
    icon: CheckCircle2,
    label: "Name Available",
  },
  payment_pending: {
    color: "text-yellow-400",
    icon: Clock,
    label: "Payment Pending",
  },
  payment_complete: {
    color: "text-green-400",
    icon: CheckCircle2,
    label: "Paid",
  },
  human_kernel_required: {
    color: "text-yellow-400",
    icon: AlertTriangle,
    label: "Identity Needed",
  },
  human_kernel_completed: {
    color: "text-green-400",
    icon: CheckCircle2,
    label: "Verified",
  },
  docs_generated: {
    color: "text-blue-400",
    icon: Building2,
    label: "Docs Ready",
  },
  state_filing_submitted: {
    color: "text-yellow-400",
    icon: Clock,
    label: "Filing Submitted",
  },
  state_confirmed: {
    color: "text-green-400",
    icon: CheckCircle2,
    label: "State Confirmed",
  },
  ein_pending: {
    color: "text-yellow-400",
    icon: Clock,
    label: "EIN Pending",
  },
  ein_issued: {
    color: "text-green-400",
    icon: CheckCircle2,
    label: "EIN Issued",
  },
  bank_pack_ready: {
    color: "text-blue-400",
    icon: Building2,
    label: "Bank Pack Ready",
  },
  active: {
    color: "text-emerald-400",
    icon: CheckCircle2,
    label: "Active",
  },
  failed: { color: "text-red-400", icon: XCircle, label: "Failed" },
};

const DEFAULT_STATE: StateDisplay = {
  color: "text-stone-400",
  icon: Clock,
  label: "Unknown",
};

/* ─── Helper to get state display ───────────────────────────── */

function getStateDisplay(status: string): StateDisplay {
  return STATE_CONFIG[status] ?? DEFAULT_STATE;
}

/* ─── Skeleton loader ───────────────────────────────────────── */

function SkeletonCard() {
  return (
    <div className="animate-pulse rounded-xl border border-stone-800/60 bg-stone-900/40 p-6">
      <div className="h-5 w-2/3 rounded bg-stone-800" />
      <div className="mt-3 h-4 w-1/3 rounded bg-stone-800/60" />
      <div className="mt-6 flex items-center justify-between">
        <div className="h-6 w-24 rounded-full bg-stone-800/40" />
        <div className="h-4 w-20 rounded bg-stone-800/40" />
      </div>
    </div>
  );
}

/* ─── Empty state ───────────────────────────────────────────── */

function EmptyState() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="mx-auto max-w-md text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full border border-stone-800 bg-stone-900/40">
          <Building2
            className="h-7 w-7 text-stone-600"
            strokeWidth={1.5}
          />
        </div>
        <h2 className="heading-display mt-6 text-xl text-stone-200">
          No entities yet
        </h2>
        <p className="mt-2 text-sm leading-relaxed text-stone-500">
          Create your first entity to get started. Formation typically
          takes 24&ndash;48 hours.
        </p>
        <Link
          to="/start"
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-bronze-500 px-6 py-2.5 text-sm font-semibold text-stone-950 transition-all duration-200 hover:bg-bronze-400 hover:shadow-lg hover:shadow-bronze-500/10"
        >
          <Plus className="h-4 w-4" />
          Create Entity
        </Link>
      </div>
    </div>
  );
}

/* ─── Order card ────────────────────────────────────────────── */

function OrderCard({
  order,
  index,
}: {
  order: EntityOrder;
  index: number;
}) {
  const state = getStateDisplay(order.status);
  const StateIcon = state.icon;
  const createdDate = new Date(order.created_at).toLocaleDateString(
    "en-US",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
    },
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.06, ease: "easeOut" }}
    >
      <Link
        to={`/dashboard/${order.id}`}
        className="group block rounded-xl border border-stone-800/60 bg-stone-900/40 p-6 transition-all duration-200 hover:border-stone-700/80 hover:bg-stone-900/70"
      >
        {/* Entity name */}
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-base font-semibold text-stone-100 group-hover:text-bronze-200 transition-colors">
            {order.entity_name}
          </h3>
          <ArrowRight className="mt-0.5 h-4 w-4 shrink-0 text-stone-700 transition-all duration-200 group-hover:text-bronze-500 group-hover:translate-x-0.5" />
        </div>

        {/* Jurisdiction badge */}
        <div className="mt-3">
          <span className="rounded-md bg-stone-800/60 px-2 py-1 text-xs font-medium text-stone-400">
            {order.jurisdiction}
          </span>
        </div>

        {/* State + date */}
        <div className="mt-5 flex items-center justify-between">
          <div className={`flex items-center gap-1.5 ${state.color}`}>
            <StateIcon className="h-4 w-4" strokeWidth={1.5} />
            <span className="text-xs font-medium">{state.label}</span>
          </div>
          <span className="text-xs text-stone-600">{createdDate}</span>
        </div>
      </Link>
    </motion.div>
  );
}

/* ─── Dashboard page ────────────────────────────────────────── */

export function Dashboard() {
  const [orders, setOrders] = useState<EntityOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await api.orders.list();
        if (!cancelled) {
          setOrders(data);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const message =
            err !== null &&
            typeof err === "object" &&
            "detail" in err &&
            typeof (err as { detail: unknown }).detail === "string"
              ? (err as { detail: string }).detail
              : "Failed to load orders.";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="relative">
      {/* Background accent */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 40% at 50% 0%, rgba(191,159,117,0.04) 0%, transparent 60%)",
        }}
      />

      <div className="relative mx-auto max-w-6xl px-6 py-16">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-bronze-500">
              Dashboard
            </p>
            <h1 className="heading-display mt-2 text-3xl text-stone-100">
              Your Entities
            </h1>
          </div>
          <Link
            to="/start"
            className="inline-flex items-center gap-2 rounded-lg bg-bronze-500 px-5 py-2.5 text-sm font-semibold text-stone-950 transition-all duration-200 hover:bg-bronze-400 hover:shadow-lg hover:shadow-bronze-500/10"
          >
            <Plus className="h-4 w-4" />
            New Entity
          </Link>
        </div>

        {/* Error */}
        {error && (
          <div className="mt-6 rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Content */}
        <div className="mt-10">
          {loading ? (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : orders.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {orders.map((order, i) => (
                <OrderCard key={order.id} order={order} index={i} />
              ))}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
