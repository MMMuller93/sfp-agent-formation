import { useState, type FormEvent } from "react";
import { CheckSquare, Square, ChevronRight, Loader2, AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";

/* ─── Types ─────────────────────────────────────────────────── */

interface Props {
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  submitting: boolean;
}

interface Attestation {
  id: string;
  text: string;
}

/* ─── Attestations ──────────────────────────────────────────── */

const ATTESTATIONS: Attestation[] = [
  {
    id: "beneficial_owner",
    text: "I am a beneficial owner of this entity, as defined under the Corporate Transparency Act (CTA), and I have the authority to make these attestations on behalf of the entity.",
  },
  {
    id: "information_accurate",
    text: "The information I have provided throughout this verification process is accurate, complete, and not misleading in any material respect.",
  },
  {
    id: "authorize_formation",
    text: "I authorize the formation of this legal entity and grant Sovereign Formation Partners the authority to act as formation agent on my behalf.",
  },
  {
    id: "cta_obligations",
    text: "I understand my ongoing reporting obligations under the Corporate Transparency Act, including the requirement to update beneficial ownership information within 30 days of any material change.",
  },
];

/* ─── Component ─────────────────────────────────────────────── */

export function KernelStepAttest({ onSubmit, submitting }: Props) {
  const [checked, setChecked] = useState<Record<string, boolean>>(
    Object.fromEntries(ATTESTATIONS.map((a) => [a.id, false])),
  );
  const [error, setError] = useState<string | null>(null);

  const allChecked = ATTESTATIONS.every((a) => checked[a.id]);

  function toggle(id: string) {
    setChecked((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!allChecked || submitting) return;
    setError(null);

    try {
      await onSubmit({
        attestations: Object.keys(checked).filter((k) => checked[k]),
        attested_at: new Date().toISOString(),
      });
    } catch (err: unknown) {
      const message =
        err !== null &&
        typeof err === "object" &&
        "detail" in err &&
        typeof (err as { detail: unknown }).detail === "string"
          ? (err as { detail: string }).detail
          : "Failed to submit attestations. Please try again.";
      setError(message);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      {/* Legal notice */}
      <div className="mb-6 flex items-start gap-3 rounded-lg border border-yellow-500/20 bg-yellow-500/5 px-4 py-3.5">
        <AlertTriangle
          className="mt-0.5 h-4 w-4 shrink-0 text-yellow-500"
          strokeWidth={1.5}
        />
        <p className="text-xs leading-relaxed text-stone-400">
          These attestations carry legal weight. By checking each box you are
          making a sworn declaration under penalty of law. Read each statement
          carefully before proceeding.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Attestation checkboxes */}
        {ATTESTATIONS.map((attestation, index) => {
          const isChecked = checked[attestation.id] ?? false;

          return (
            <motion.div
              key={attestation.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
              className={`rounded-xl border p-5 transition-all duration-200 ${
                isChecked
                  ? "border-bronze-500/40 bg-bronze-500/5"
                  : "border-stone-800/60 bg-stone-900/40"
              }`}
            >
              <label className="flex cursor-pointer items-start gap-4">
                {/* Checkbox button */}
                <button
                  type="button"
                  onClick={() => toggle(attestation.id)}
                  className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded transition-colors ${
                    isChecked
                      ? "text-bronze-400"
                      : "text-stone-700 hover:text-stone-500"
                  }`}
                  aria-label={`Attest: ${attestation.text.slice(0, 40)}...`}
                >
                  {isChecked ? (
                    <CheckSquare className="h-5 w-5" strokeWidth={1.5} />
                  ) : (
                    <Square className="h-5 w-5" strokeWidth={1.5} />
                  )}
                </button>

                {/* Text */}
                <p
                  className={`text-sm leading-relaxed transition-colors ${
                    isChecked ? "text-stone-200" : "text-stone-400"
                  }`}
                >
                  {attestation.text}
                </p>
              </label>
            </motion.div>
          );
        })}

        {/* Progress indicator */}
        <div className="flex items-center justify-between rounded-lg border border-stone-800/40 bg-stone-900/20 px-4 py-3">
          <span className="text-xs text-stone-500">Attestations confirmed</span>
          <span
            className={`text-sm font-semibold tabular-nums ${
              allChecked ? "text-emerald-400" : "text-stone-400"
            }`}
          >
            {ATTESTATIONS.filter((a) => checked[a.id]).length} / {ATTESTATIONS.length}
          </span>
        </div>

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
            disabled={!allChecked || submitting}
            className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-bronze-500 px-6 py-3 text-sm font-semibold text-stone-950 transition-all duration-200 hover:bg-bronze-400 hover:shadow-lg hover:shadow-bronze-500/10 disabled:opacity-40 disabled:hover:bg-bronze-500"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting attestations...
              </>
            ) : (
              <>
                Complete Verification
                <ChevronRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </motion.div>
  );
}
