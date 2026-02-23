import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  FileText,
  Download,
  ChevronRight,
} from "lucide-react";
import { api, type OrderResponse } from "@/lib/api";

/* ─── State machine + display ───────────────────────────────── */

interface StateDisplay {
  color: string;
  bgColor: string;
  icon: typeof Building2;
  label: string;
}

const STATE_CONFIG: Record<string, StateDisplay> = {
  draft: {
    color: "text-stone-400",
    bgColor: "bg-stone-400",
    icon: Clock,
    label: "Draft",
  },
  intake_complete: {
    color: "text-blue-400",
    bgColor: "bg-blue-400",
    icon: Building2,
    label: "Intake Complete",
  },
  name_check_passed: {
    color: "text-blue-400",
    bgColor: "bg-blue-400",
    icon: CheckCircle2,
    label: "Name Available",
  },
  payment_pending: {
    color: "text-yellow-400",
    bgColor: "bg-yellow-400",
    icon: Clock,
    label: "Payment Pending",
  },
  payment_complete: {
    color: "text-green-400",
    bgColor: "bg-green-400",
    icon: CheckCircle2,
    label: "Paid",
  },
  human_kernel_required: {
    color: "text-yellow-400",
    bgColor: "bg-yellow-400",
    icon: AlertTriangle,
    label: "Identity Verification Needed",
  },
  human_kernel_completed: {
    color: "text-green-400",
    bgColor: "bg-green-400",
    icon: CheckCircle2,
    label: "Identity Verified",
  },
  docs_generated: {
    color: "text-blue-400",
    bgColor: "bg-blue-400",
    icon: FileText,
    label: "Documents Ready",
  },
  state_filing_submitted: {
    color: "text-yellow-400",
    bgColor: "bg-yellow-400",
    icon: Clock,
    label: "Filing Submitted",
  },
  state_confirmed: {
    color: "text-green-400",
    bgColor: "bg-green-400",
    icon: CheckCircle2,
    label: "State Confirmed",
  },
  ein_pending: {
    color: "text-yellow-400",
    bgColor: "bg-yellow-400",
    icon: Clock,
    label: "EIN Pending",
  },
  ein_issued: {
    color: "text-green-400",
    bgColor: "bg-green-400",
    icon: CheckCircle2,
    label: "EIN Issued",
  },
  bank_pack_ready: {
    color: "text-blue-400",
    bgColor: "bg-blue-400",
    icon: Building2,
    label: "Bank Pack Ready",
  },
  active: {
    color: "text-emerald-400",
    bgColor: "bg-emerald-400",
    icon: CheckCircle2,
    label: "Active",
  },
  failed: {
    color: "text-red-400",
    bgColor: "bg-red-400",
    icon: XCircle,
    label: "Failed",
  },
};

const DEFAULT_STATE: StateDisplay = {
  color: "text-stone-400",
  bgColor: "bg-stone-400",
  icon: Clock,
  label: "Unknown",
};

/** Ordered progression of states for the timeline */
const STATE_SEQUENCE = [
  "draft",
  "intake_complete",
  "name_check_passed",
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
];

function getStateDisplay(status: string): StateDisplay {
  return STATE_CONFIG[status] ?? DEFAULT_STATE;
}

/** Determine the index of the current state within the ordered progression */
function getCurrentStateIndex(status: string): number {
  const idx = STATE_SEQUENCE.indexOf(status);
  return idx >= 0 ? idx : -1;
}

/* ─── Next actions for a given state ────────────────────────── */

interface NextAction {
  title: string;
  description: string;
  actionLabel: string;
  href: string;
}

function getNextActions(order: OrderResponse): NextAction[] {
  const actions: NextAction[] = [];

  switch (order.state) {
    case "draft":
      actions.push({
        title: "Complete Intake",
        description:
          "Finish filling out entity formation details to proceed.",
        actionLabel: "Edit Order",
        href: "/start",
      });
      break;
    case "payment_pending":
      actions.push({
        title: "Complete Payment",
        description:
          "Payment is required to begin the formation process.",
        actionLabel: "Pay Now",
        href: `/dashboard/${order.id}`,
      });
      break;
    case "human_kernel_required":
      actions.push({
        title: "Verify Identity",
        description:
          "A compliance officer needs to verify beneficial owner identity.",
        actionLabel: "Start Verification",
        href: `/kernel/${order.id}`,
      });
      break;
    case "active":
      actions.push({
        title: "View Documents",
        description:
          "Your entity is fully formed. View and download your formation documents.",
        actionLabel: "View Docs",
        href: `/dashboard/${order.id}`,
      });
      break;
    case "failed":
      actions.push({
        title: "Contact Support",
        description:
          "Something went wrong with your formation. Please reach out for assistance.",
        actionLabel: "Get Help",
        href: "mailto:support@sfp.legal",
      });
      break;
    default:
      // In-progress states: no user action required
      break;
  }

  return actions;
}

/* ─── Placeholder documents ─────────────────────────────────── */

interface Document {
  name: string;
  type: string;
  available: boolean;
}

function getDocuments(status: string): Document[] {
  const stateIdx = getCurrentStateIndex(status);
  const docsIdx = STATE_SEQUENCE.indexOf("docs_generated");
  const activeIdx = STATE_SEQUENCE.indexOf("active");

  return [
    {
      name: "Certificate of Formation",
      type: "PDF",
      available: stateIdx >= activeIdx,
    },
    {
      name: "Operating Agreement",
      type: "PDF",
      available: stateIdx >= docsIdx,
    },
    {
      name: "EIN Confirmation Letter",
      type: "PDF",
      available: stateIdx >= STATE_SEQUENCE.indexOf("ein_issued"),
    },
    {
      name: "Registered Agent Appointment",
      type: "PDF",
      available: stateIdx >= docsIdx,
    },
  ];
}

/* ─── Skeleton loader ───────────────────────────────────────── */

function DetailSkeleton() {
  return (
    <div className="animate-pulse space-y-8">
      <div className="h-8 w-1/2 rounded bg-stone-800" />
      <div className="h-5 w-1/3 rounded bg-stone-800/60" />
      <div className="space-y-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-12 rounded-lg bg-stone-800/30" />
        ))}
      </div>
    </div>
  );
}

/* ─── Progress timeline ─────────────────────────────────────── */

function ProgressTimeline({ currentStatus }: { currentStatus: string }) {
  const currentIdx = getCurrentStateIndex(currentStatus);

  // Show a meaningful subset of the timeline (skip some intermediate states)
  const timelineStates = [
    "draft",
    "intake_complete",
    "payment_complete",
    "human_kernel_completed",
    "docs_generated",
    "state_confirmed",
    "ein_issued",
    "active",
  ];

  return (
    <div className="rounded-xl border border-stone-800/60 bg-stone-900/40 p-6">
      <h2 className="text-sm font-semibold text-stone-300">
        Formation Progress
      </h2>

      <div className="mt-6 space-y-0">
        {timelineStates.map((stateKey, index) => {
          const stateDisplay = getStateDisplay(stateKey);
          const stateIdx = getCurrentStateIndex(stateKey);
          const isComplete = stateIdx <= currentIdx && stateIdx >= 0;
          const isCurrent = stateKey === currentStatus;
          const isLast = index === timelineStates.length - 1;
          const Icon = stateDisplay.icon;

          return (
            <div key={stateKey} className="flex gap-4">
              {/* Timeline track */}
              <div className="flex flex-col items-center">
                <div
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full border-2 transition-all ${
                    isCurrent
                      ? `border-current ${stateDisplay.color} bg-stone-900`
                      : isComplete
                        ? "border-bronze-500 bg-bronze-500/10 text-bronze-400"
                        : "border-stone-700 bg-stone-900 text-stone-700"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" strokeWidth={2} />
                </div>
                {!isLast && (
                  <div
                    className={`w-px flex-1 min-h-6 ${
                      isComplete && !isCurrent
                        ? "bg-bronze-500/40"
                        : "bg-stone-800"
                    }`}
                  />
                )}
              </div>

              {/* Label */}
              <div className={`pb-5 ${isLast ? "pb-0" : ""}`}>
                <p
                  className={`text-sm font-medium ${
                    isCurrent
                      ? stateDisplay.color
                      : isComplete
                        ? "text-stone-300"
                        : "text-stone-600"
                  }`}
                >
                  {stateDisplay.label}
                </p>
                {isCurrent && (
                  <p className="mt-0.5 text-xs text-stone-500">
                    Current step
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─── Next actions card ─────────────────────────────────────── */

function NextActionsCard({ order }: { order: OrderResponse }) {
  const actions = getNextActions(order);

  if (actions.length === 0) {
    return (
      <div className="rounded-xl border border-stone-800/60 bg-stone-900/40 p-6">
        <h2 className="text-sm font-semibold text-stone-300">
          Next Steps
        </h2>
        <div className="mt-4 flex items-center gap-3 rounded-lg border border-stone-800/40 bg-stone-900/20 px-4 py-4">
          <Clock
            className="h-5 w-5 shrink-0 text-stone-600"
            strokeWidth={1.5}
          />
          <div>
            <p className="text-sm text-stone-400">
              No action required
            </p>
            <p className="mt-0.5 text-xs text-stone-600">
              Your order is being processed. We&apos;ll notify you when
              the next step is ready.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-stone-800/60 bg-stone-900/40 p-6">
      <h2 className="text-sm font-semibold text-stone-300">
        Required Actions
      </h2>
      <div className="mt-4 space-y-3">
        {actions.map((action) => (
          <div
            key={action.title}
            className="rounded-lg border border-bronze-500/20 bg-bronze-500/5 px-4 py-4"
          >
            <h3 className="text-sm font-semibold text-stone-200">
              {action.title}
            </h3>
            <p className="mt-1 text-xs leading-relaxed text-stone-500">
              {action.description}
            </p>
            <Link
              to={action.href}
              className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-bronze-500 px-3.5 py-1.5 text-xs font-semibold text-stone-950 transition-colors hover:bg-bronze-400"
            >
              {action.actionLabel}
              <ChevronRight className="h-3 w-3" />
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Documents card ────────────────────────────────────────── */

function DocumentsCard({ status }: { status: string }) {
  const documents = getDocuments(status);
  const hasAny = documents.some((d) => d.available);

  return (
    <div className="rounded-xl border border-stone-800/60 bg-stone-900/40 p-6">
      <h2 className="text-sm font-semibold text-stone-300">Documents</h2>

      {!hasAny ? (
        <p className="mt-4 text-sm text-stone-600">
          Documents will appear here once generated.
        </p>
      ) : (
        <div className="mt-4 space-y-2">
          {documents.map((doc) => (
            <div
              key={doc.name}
              className={`flex items-center justify-between rounded-lg border px-4 py-3 ${
                doc.available
                  ? "border-stone-800/40 bg-stone-900/20"
                  : "border-stone-800/20 bg-stone-900/10 opacity-50"
              }`}
            >
              <div className="flex items-center gap-3">
                <FileText
                  className={`h-4 w-4 ${
                    doc.available ? "text-bronze-500" : "text-stone-700"
                  }`}
                  strokeWidth={1.5}
                />
                <div>
                  <p
                    className={`text-sm ${
                      doc.available
                        ? "text-stone-200"
                        : "text-stone-600"
                    }`}
                  >
                    {doc.name}
                  </p>
                  <p className="text-xs text-stone-600">{doc.type}</p>
                </div>
              </div>
              {doc.available && (
                <button
                  type="button"
                  className="rounded-md p-1.5 text-stone-500 transition-colors hover:bg-stone-800 hover:text-stone-300"
                >
                  <Download className="h-4 w-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Order Detail page ─────────────────────────────────────── */

export function OrderDetail() {
  const { orderId } = useParams<{ orderId: string }>();
  const [order, setOrder] = useState<OrderResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orderId) return;

    let cancelled = false;

    async function load() {
      try {
        const data = await api.orders.get(orderId!);
        if (!cancelled) {
          setOrder(data);
        }
      } catch (err: unknown) {
        if (!cancelled) {
          const message =
            err !== null &&
            typeof err === "object" &&
            "detail" in err &&
            typeof (err as { detail: unknown }).detail === "string"
              ? (err as { detail: string }).detail
              : "Failed to load order.";
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
  }, [orderId]);

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl px-6 py-16">
        <DetailSkeleton />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <XCircle className="mx-auto h-10 w-10 text-red-400/60" />
          <p className="mt-4 text-sm text-red-400">
            {error ?? "Order not found."}
          </p>
          <Link
            to="/dashboard"
            className="mt-4 inline-flex items-center gap-1.5 text-sm text-stone-400 transition-colors hover:text-stone-200"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const stateDisplay = getStateDisplay(order.state);
  const StateIcon = stateDisplay.icon;
  const createdDate = new Date(order.created_at).toLocaleDateString(
    "en-US",
    {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    },
  );

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

      <div className="relative mx-auto max-w-5xl px-6 py-16">
        {/* Back link */}
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-stone-500 transition-colors hover:text-stone-300"
        >
          <ArrowLeft className="h-4 w-4" />
          All Entities
        </Link>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className="mt-6"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="heading-display text-3xl text-stone-100">
                {order.requested_name}
              </h1>
              <div className="mt-2 flex flex-wrap items-center gap-3">
                <span className="rounded-md bg-stone-800/60 px-2.5 py-1 text-xs font-medium text-stone-400">
                  {order.jurisdiction}
                </span>
                <span className="text-xs text-stone-600">
                  Created {createdDate}
                </span>
              </div>
            </div>

            {/* State badge */}
            <div
              className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium ${stateDisplay.color} ${
                order.state === "active"
                  ? "border-emerald-500/30 bg-emerald-500/5"
                  : order.state === "failed"
                    ? "border-red-500/30 bg-red-500/5"
                    : "border-stone-700 bg-stone-900/60"
              }`}
            >
              <StateIcon className="h-4 w-4" strokeWidth={1.5} />
              {stateDisplay.label}
            </div>
          </div>
        </motion.div>

        {/* Content grid */}
        <div className="mt-10 grid gap-6 lg:grid-cols-5">
          {/* Timeline — takes 2 columns */}
          <div className="lg:col-span-2">
            <ProgressTimeline currentStatus={order.state} />
          </div>

          {/* Right column — takes 3 columns */}
          <div className="space-y-6 lg:col-span-3">
            <NextActionsCard order={order} />
            <DocumentsCard status={order.state} />
          </div>
        </div>
      </div>
    </section>
  );
}
