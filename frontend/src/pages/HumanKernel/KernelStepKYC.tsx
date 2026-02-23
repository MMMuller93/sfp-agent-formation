import { useState, useEffect } from "react";
import { CheckCircle2, Loader2, ChevronRight, Shield } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

/* ─── Types ─────────────────────────────────────────────────── */

interface Props {
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  submitting: boolean;
}

type KYCState = "verifying" | "verified";

/* ─── Component ─────────────────────────────────────────────── */

export function KernelStepKYC({ onSubmit, submitting }: Props) {
  const [kycState, setKycState] = useState<KYCState>("verifying");
  const [error, setError] = useState<string | null>(null);

  // Simulate the identity verification check — in production this would
  // integrate with Persona or Jumio via a webhook/polling mechanism.
  useEffect(() => {
    const timer = setTimeout(() => {
      setKycState("verified");
    }, 2200);

    return () => clearTimeout(timer);
  }, []);

  async function handleProceed() {
    if (kycState !== "verified" || submitting) return;
    setError(null);

    try {
      await onSubmit({ kyc_status: "verified", provider: "stub" });
    } catch (err: unknown) {
      const message =
        err !== null &&
        typeof err === "object" &&
        "detail" in err &&
        typeof (err as { detail: unknown }).detail === "string"
          ? (err as { detail: string }).detail
          : "Failed to proceed. Please try again.";
      setError(message);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      {/* KYC status card */}
      <div className="rounded-xl border border-stone-800/60 bg-stone-900/40 p-8">
        <AnimatePresence mode="wait">
          {kycState === "verifying" ? (
            <motion.div
              key="verifying"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col items-center py-8 text-center"
            >
              <div className="relative flex h-16 w-16 items-center justify-center">
                {/* Outer pulsing ring */}
                <div className="absolute inset-0 animate-ping rounded-full border border-bronze-500/30" />
                <div className="flex h-16 w-16 items-center justify-center rounded-full border border-stone-700 bg-stone-900">
                  <Loader2 className="h-7 w-7 animate-spin text-bronze-500" strokeWidth={1.5} />
                </div>
              </div>
              <h3 className="heading-display mt-6 text-xl text-stone-100">
                Verifying your identity
              </h3>
              <p className="mt-2 max-w-xs text-sm leading-relaxed text-stone-500">
                We are cross-referencing your information against identity
                verification databases. This takes just a moment.
              </p>

              {/* Step indicators */}
              <div className="mt-8 space-y-2.5 text-left">
                {[
                  "Checking personal information",
                  "Running compliance screening",
                  "Confirming identity",
                ].map((label, i) => (
                  <div key={i} className="flex items-center gap-2.5">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-bronze-500/60" strokeWidth={2} />
                    <span className="text-xs text-stone-500">{label}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="verified"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="flex flex-col items-center py-8 text-center"
            >
              <div className="flex h-16 w-16 items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/10">
                <CheckCircle2 className="h-8 w-8 text-emerald-400" strokeWidth={1.5} />
              </div>
              <h3 className="heading-display mt-6 text-xl text-stone-100">
                Identity verified
              </h3>
              <p className="mt-2 max-w-xs text-sm leading-relaxed text-stone-500">
                Your identity has been verified successfully. You can now
                proceed to review and sign your formation documents.
              </p>

              {/* Verification detail */}
              <div className="mt-8 flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/5 px-4 py-2">
                <Shield className="h-3.5 w-3.5 text-emerald-400" strokeWidth={1.5} />
                <span className="text-xs font-medium text-emerald-400">
                  KYC check passed
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Production note */}
      <p className="mt-4 text-center text-xs text-stone-600">
        In production, this step integrates with Persona or Jumio for
        live document and biometric verification.
      </p>

      {/* Error */}
      {error && (
        <div className="mt-4 rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Proceed button — only shown after verification */}
      <AnimatePresence>
        {kycState === "verified" && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: 0.1 }}
            className="mt-6"
          >
            <button
              type="button"
              onClick={() => void handleProceed()}
              disabled={submitting}
              className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-bronze-500 px-6 py-3 text-sm font-semibold text-stone-950 transition-all duration-200 hover:bg-bronze-400 hover:shadow-lg hover:shadow-bronze-500/10 disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  Continue to Document Signing
                  <ChevronRight className="h-4 w-4" />
                </>
              )}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
