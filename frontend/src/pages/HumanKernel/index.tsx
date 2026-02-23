import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  User,
  ShieldCheck,
  FileSignature,
  ClipboardCheck,
  Shield,
} from "lucide-react";
import { api, type KernelSessionStatus, type KernelStep } from "@/lib/api";
import { KernelStepPII } from "./KernelStepPII";
import { KernelStepKYC } from "./KernelStepKYC";
import { KernelStepSign } from "./KernelStepSign";
import { KernelStepAttest } from "./KernelStepAttest";
import { KernelComplete } from "./KernelComplete";
import { KernelExpired } from "./KernelExpired";

/* ─── Step configuration ────────────────────────────────────── */

interface StepConfig {
  id: KernelStep;
  label: string;
  title: string;
  description: string;
  icon: typeof User;
}

const STEPS: StepConfig[] = [
  {
    id: "pii_collection",
    label: "Identity",
    title: "Personal Information",
    description:
      "Provide your personal identifying information. All data is encrypted before transmission.",
    icon: User,
  },
  {
    id: "kyc_verification",
    label: "KYC",
    title: "Identity Verification",
    description:
      "We verify your identity against trusted databases to satisfy compliance requirements.",
    icon: ShieldCheck,
  },
  {
    id: "document_signing",
    label: "Documents",
    title: "Review & Sign Documents",
    description:
      "Review and sign your formation documents. Your typed signature serves as your electronic signature.",
    icon: FileSignature,
  },
  {
    id: "attestation",
    label: "Attestation",
    title: "Final Attestations",
    description:
      "Make your final attestations regarding beneficial ownership and compliance obligations.",
    icon: ClipboardCheck,
  },
];

/* ─── Loading skeleton ──────────────────────────────────────── */

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-8">
      <div className="mx-auto h-4 w-48 rounded bg-stone-800" />
      <div className="mx-auto flex max-w-md justify-between">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex flex-col items-center gap-2">
            <div className="h-9 w-9 rounded-full bg-stone-800" />
            <div className="h-3 w-12 rounded bg-stone-800/60" />
          </div>
        ))}
      </div>
      <div className="mx-auto max-w-lg rounded-xl border border-stone-800/60 bg-stone-900/40 p-8 space-y-4">
        <div className="h-6 w-1/2 rounded bg-stone-800" />
        <div className="h-4 w-3/4 rounded bg-stone-800/60" />
        <div className="mt-6 h-12 rounded-lg bg-stone-800/40" />
        <div className="h-12 rounded-lg bg-stone-800/30" />
        <div className="h-12 rounded-lg bg-stone-800/20" />
      </div>
    </div>
  );
}

/* ─── Progress bar ──────────────────────────────────────────── */

function KernelProgressBar({
  steps,
  currentStepId,
  completedStepIds,
}: {
  steps: StepConfig[];
  currentStepId: KernelStep;
  completedStepIds: string[];
}) {
  return (
    <div className="mx-auto mb-10 flex max-w-lg items-center justify-between">
      {steps.map((step, index) => {
        const Icon = step.icon;
        const isComplete = completedStepIds.includes(step.id);
        const isActive = step.id === currentStepId;

        return (
          <div key={step.id} className="flex items-center">
            {/* Connector line */}
            {index > 0 && (
              <div
                className={`mx-2 h-px w-8 sm:w-12 ${
                  completedStepIds.includes(steps[index - 1]?.id ?? "")
                    ? "bg-bronze-500"
                    : "bg-stone-800"
                }`}
              />
            )}

            {/* Step dot */}
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`flex h-9 w-9 items-center justify-center rounded-full border-2 transition-all duration-300 ${
                  isComplete
                    ? "border-bronze-500 bg-bronze-500/10 text-bronze-400"
                    : isActive
                      ? "border-bronze-500 bg-stone-900 text-bronze-400"
                      : "border-stone-700 bg-stone-900 text-stone-600"
                }`}
              >
                <Icon className="h-4 w-4" strokeWidth={1.5} />
              </div>
              <span
                className={`hidden text-[11px] font-medium sm:block ${
                  isActive
                    ? "text-bronze-400"
                    : isComplete
                      ? "text-stone-400"
                      : "text-stone-600"
                }`}
              >
                {step.label}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ─── Main HumanKernel orchestrator ─────────────────────────── */

type ViewState = "loading" | "error" | "expired" | "complete" | "active";

export function HumanKernel() {
  const { token } = useParams<{ token: string }>();

  const [viewState, setViewState] = useState<ViewState>("loading");
  const [session, setSession] = useState<KernelSessionStatus | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [direction, setDirection] = useState(1);

  // Fetch session on mount
  useEffect(() => {
    if (!token) {
      setLoadError("Invalid verification link — no token provided.");
      setViewState("error");
      return;
    }

    let cancelled = false;

    async function load() {
      try {
        const data = await api.kernel.getSession(token!);
        if (cancelled) return;

        setSession(data);

        if (data.is_expired || data.status === "expired") {
          setViewState("expired");
        } else if (data.status === "completed" || data.remaining_steps.length === 0) {
          setViewState("complete");
        } else {
          setViewState("active");
        }
      } catch (err: unknown) {
        if (cancelled) return;
        const message =
          err !== null &&
          typeof err === "object" &&
          "detail" in err &&
          typeof (err as { detail: unknown }).detail === "string"
            ? (err as { detail: string }).detail
            : "Failed to load verification session.";

        // Treat 404/410 as expired
        if (
          err !== null &&
          typeof err === "object" &&
          "status" in err &&
          (err as { status: number }).status === 410
        ) {
          setViewState("expired");
        } else {
          setLoadError(message);
          setViewState("error");
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  // Determine the current active step
  function getCurrentStep(): StepConfig | null {
    if (!session) return null;
    const nextStepId = session.remaining_steps[0] as KernelStep | undefined;
    return STEPS.find((s) => s.id === nextStepId) ?? null;
  }

  // Submit a step to the API
  async function handleStepSubmit(data: Record<string, unknown>) {
    if (!token || !session || submitting) return;

    const currentStep = getCurrentStep();
    if (!currentStep) return;

    setSubmitting(true);
    try {
      const response = await api.kernel.submitStep(token, {
        step: currentStep.id,
        data,
      });

      setDirection(1);

      if (response.all_complete) {
        setViewState("complete");
      } else {
        // Update session state with new completed/remaining steps
        setSession((prev) =>
          prev
            ? {
                ...prev,
                completed_steps: response.completed_steps,
                remaining_steps: response.remaining_steps,
              }
            : prev,
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  const currentStep = getCurrentStep();
  const completedStepIds = session?.completed_steps ?? [];

  // ── Render states ──

  if (viewState === "loading") {
    return (
      <section className="relative min-h-[80vh]">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 80% 40% at 50% 0%, rgba(191,159,117,0.04) 0%, transparent 60%)",
          }}
        />
        <div className="relative mx-auto max-w-4xl px-6 py-16">
          <LoadingSkeleton />
        </div>
      </section>
    );
  }

  if (viewState === "expired") {
    return (
      <section className="relative min-h-[80vh]">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 80% 40% at 50% 0%, rgba(191,159,117,0.03) 0%, transparent 60%)",
          }}
        />
        <div className="relative mx-auto max-w-lg px-6 py-16">
          <KernelExpired />
        </div>
      </section>
    );
  }

  if (viewState === "complete") {
    return (
      <section className="relative min-h-[80vh]">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(ellipse 80% 40% at 50% 0%, rgba(52,211,153,0.03) 0%, transparent 60%)",
          }}
        />
        <div className="relative mx-auto max-w-lg px-6 py-16">
          <KernelComplete />
        </div>
      </section>
    );
  }

  if (viewState === "error" || !currentStep) {
    return (
      <section className="relative min-h-[80vh]">
        <div className="relative mx-auto max-w-lg px-6 py-16 text-center">
          <p className="text-sm text-red-400">
            {loadError ?? "Unable to load this verification session."}
          </p>
          <a
            href="mailto:support@sfp.legal"
            className="mt-4 inline-block text-sm text-stone-400 underline hover:text-stone-200"
          >
            Contact support
          </a>
        </div>
      </section>
    );
  }

  // ── Active step ──

  return (
    <section className="relative min-h-[80vh]">
      {/* Background accent */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 40% at 50% 0%, rgba(191,159,117,0.05) 0%, transparent 60%)",
        }}
      />

      <div className="relative mx-auto max-w-4xl px-6 py-16">
        {/* Header */}
        <div className="mb-10 text-center">
          <div className="mb-4 flex justify-center">
            <div className="flex items-center gap-2 rounded-full border border-stone-800/60 bg-stone-900/60 px-4 py-2">
              <Shield className="h-3.5 w-3.5 text-bronze-500" strokeWidth={1.5} />
              <span className="text-xs font-medium text-stone-400">
                Secure Verification Portal
              </span>
            </div>
          </div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-bronze-500">
            Entity Formation
          </p>
          <h1 className="heading-display mt-2 text-3xl text-stone-100">
            Identity Verification
          </h1>
        </div>

        {/* Progress bar */}
        <KernelProgressBar
          steps={STEPS}
          currentStepId={currentStep.id}
          completedStepIds={completedStepIds}
        />

        {/* Step card */}
        <div className="mx-auto max-w-lg">
          {/* Step header */}
          <motion.div
            key={`header-${currentStep.id}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="mb-6"
          >
            <h2 className="heading-display text-2xl text-stone-100">
              {currentStep.title}
            </h2>
            <p className="mt-1.5 text-sm leading-relaxed text-stone-500">
              {currentStep.description}
            </p>
          </motion.div>

          {/* Step content with slide animation */}
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={currentStep.id}
              custom={direction}
              initial={{ x: direction > 0 ? 60 : -60, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: direction > 0 ? -60 : 60, opacity: 0 }}
              transition={{ duration: 0.25, ease: "easeInOut" }}
            >
              {currentStep.id === "pii_collection" && (
                <KernelStepPII
                  onSubmit={handleStepSubmit}
                  submitting={submitting}
                />
              )}
              {currentStep.id === "kyc_verification" && (
                <KernelStepKYC
                  onSubmit={handleStepSubmit}
                  submitting={submitting}
                />
              )}
              {currentStep.id === "document_signing" && (
                <KernelStepSign
                  onSubmit={handleStepSubmit}
                  submitting={submitting}
                />
              )}
              {currentStep.id === "attestation" && (
                <KernelStepAttest
                  onSubmit={handleStepSubmit}
                  submitting={submitting}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
