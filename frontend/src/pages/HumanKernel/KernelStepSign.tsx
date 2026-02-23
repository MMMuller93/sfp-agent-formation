import { useState, type FormEvent } from "react";
import { FileText, ExternalLink, CheckSquare, Square, ChevronRight, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

/* ─── Types ─────────────────────────────────────────────────── */

interface Document {
  id: string;
  name: string;
  description: string;
  /** Stub URL — in production this would be a signed S3 URL */
  reviewUrl: string;
}

interface Props {
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  submitting: boolean;
}

/* ─── Documents list ────────────────────────────────────────── */

const DOCUMENTS: Document[] = [
  {
    id: "operating_agreement",
    name: "Operating Agreement",
    description:
      "Governs the internal operations, member rights, and management structure of the entity.",
    reviewUrl: "#operating-agreement",
  },
  {
    id: "agent_authority_schedule",
    name: "Agent Authority Schedule",
    description:
      "Defines the scope of authority granted to the AI agent to act on behalf of the entity.",
    reviewUrl: "#agent-authority-schedule",
  },
];

/* ─── Component ─────────────────────────────────────────────── */

export function KernelStepSign({ onSubmit, submitting }: Props) {
  const [reviewed, setReviewed] = useState<Record<string, boolean>>(
    Object.fromEntries(DOCUMENTS.map((d) => [d.id, false])),
  );
  const [signature, setSignature] = useState("");
  const [error, setError] = useState<string | null>(null);

  const allReviewed = DOCUMENTS.every((d) => reviewed[d.id]);
  const signatureValid = signature.trim().length >= 2;
  const canProceed = allReviewed && signatureValid;

  function toggleReviewed(id: string) {
    setReviewed((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canProceed || submitting) return;
    setError(null);

    try {
      await onSubmit({
        documents_reviewed: Object.keys(reviewed).filter((k) => reviewed[k]),
        typed_signature: signature.trim(),
        signed_at: new Date().toISOString(),
      });
    } catch (err: unknown) {
      const message =
        err !== null &&
        typeof err === "object" &&
        "detail" in err &&
        typeof (err as { detail: unknown }).detail === "string"
          ? (err as { detail: string }).detail
          : "Failed to submit signatures. Please try again.";
      setError(message);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Documents to review */}
        <div className="space-y-3">
          <p className="text-sm font-medium text-stone-300">
            Formation Documents
          </p>
          <p className="text-xs text-stone-600">
            Review each document before checking the box to confirm you have
            read it.
          </p>

          {DOCUMENTS.map((doc) => {
            const isReviewed = reviewed[doc.id] ?? false;

            return (
              <div
                key={doc.id}
                className={`rounded-xl border p-5 transition-all duration-200 ${
                  isReviewed
                    ? "border-bronze-500/40 bg-bronze-500/5"
                    : "border-stone-800/60 bg-stone-900/40"
                }`}
              >
                <div className="flex items-start gap-4">
                  <div
                    className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${
                      isReviewed
                        ? "border-bronze-500/40 bg-bronze-500/10"
                        : "border-stone-800 bg-stone-900"
                    }`}
                  >
                    <FileText
                      className={`h-4 w-4 ${isReviewed ? "text-bronze-400" : "text-stone-600"}`}
                      strokeWidth={1.5}
                    />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <h3 className="text-sm font-semibold text-stone-200">
                        {doc.name}
                      </h3>
                      <a
                        href={doc.reviewUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 rounded-md border border-stone-700 px-3 py-1.5 text-xs font-medium text-stone-300 transition-colors hover:border-stone-600 hover:text-stone-100"
                        onClick={(e) => {
                          // Stub: prevent navigation in dev
                          if (doc.reviewUrl.startsWith("#")) {
                            e.preventDefault();
                          }
                        }}
                      >
                        Review
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                    <p className="mt-1.5 text-xs leading-relaxed text-stone-500">
                      {doc.description}
                    </p>

                    {/* Review checkbox */}
                    <label className="mt-4 flex cursor-pointer items-center gap-2.5">
                      <button
                        type="button"
                        onClick={() => toggleReviewed(doc.id)}
                        className={`flex h-4 w-4 shrink-0 items-center justify-center rounded transition-colors ${
                          isReviewed
                            ? "text-bronze-400"
                            : "text-stone-700 hover:text-stone-500"
                        }`}
                        aria-label={`Mark ${doc.name} as reviewed`}
                      >
                        {isReviewed ? (
                          <CheckSquare className="h-4 w-4" strokeWidth={1.5} />
                        ) : (
                          <Square className="h-4 w-4" strokeWidth={1.5} />
                        )}
                      </button>
                      <span className="text-xs text-stone-400">
                        I have reviewed this document
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Signature */}
        <div>
          <label
            htmlFor="signature"
            className="block text-sm font-medium text-stone-300"
          >
            Typed Signature
          </label>
          <p className="mt-1 text-xs text-stone-600">
            Type your full legal name as your electronic signature. By signing
            you agree to all reviewed documents.
          </p>
          <input
            id="signature"
            type="text"
            value={signature}
            onChange={(e) => setSignature(e.target.value)}
            placeholder="Your full legal name"
            autoComplete="name"
            className="mt-2 block w-full rounded-lg border border-stone-800 bg-stone-900/60 px-3.5 py-2.5 font-serif text-base italic text-stone-100 placeholder:font-sans placeholder:not-italic placeholder:text-stone-600 focus:border-bronze-500 focus:outline-none focus:ring-1 focus:ring-bronze-500 transition-colors"
          />
          {signatureValid && (
            <p className="mt-1.5 text-xs text-stone-600">
              Signature: <span className="font-serif italic text-stone-400">{signature}</span>
            </p>
          )}
        </div>

        {/* Validation hint */}
        {!allReviewed && (
          <p className="text-xs text-yellow-500/80">
            Please review and confirm all documents before proceeding.
          </p>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Submit */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={!canProceed || submitting}
            className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-bronze-500 px-6 py-3 text-sm font-semibold text-stone-950 transition-all duration-200 hover:bg-bronze-400 hover:shadow-lg hover:shadow-bronze-500/10 disabled:opacity-40 disabled:hover:bg-bronze-500"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting signatures...
              </>
            ) : (
              <>
                Sign Documents
                <ChevronRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </motion.div>
  );
}
