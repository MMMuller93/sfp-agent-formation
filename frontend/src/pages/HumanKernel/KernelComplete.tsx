import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { CheckCircle2, ArrowRight } from "lucide-react";

/* ─── Component ─────────────────────────────────────────────── */

export function KernelComplete() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className="flex flex-col items-center py-12 text-center"
    >
      {/* Animated checkmark */}
      <div className="relative">
        {/* Outer glow ring */}
        <motion.div
          initial={{ scale: 0.6, opacity: 0 }}
          animate={{ scale: 1.4, opacity: 0 }}
          transition={{ duration: 1.2, ease: "easeOut", delay: 0.3 }}
          className="absolute inset-0 rounded-full bg-emerald-500/20"
        />
        {/* Icon container */}
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.4, ease: "easeOut", delay: 0.1 }}
          className="flex h-20 w-20 items-center justify-center rounded-full border border-emerald-500/40 bg-emerald-500/10"
        >
          <CheckCircle2 className="h-10 w-10 text-emerald-400" strokeWidth={1.5} />
        </motion.div>
      </div>

      {/* Heading */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut", delay: 0.25 }}
        className="mt-8"
      >
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-bronze-500">
          Verification Complete
        </p>
        <h2 className="heading-display mt-3 text-3xl text-stone-100">
          Your verification is complete
        </h2>
        <p className="mx-auto mt-4 max-w-sm text-sm leading-relaxed text-stone-500">
          All required steps have been completed. The formation agent has been
          notified and will proceed with your entity formation.
        </p>
      </motion.div>

      {/* Status items */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut", delay: 0.4 }}
        className="mt-10 grid w-full max-w-sm gap-2.5"
      >
        {[
          "Identity information collected",
          "KYC verification passed",
          "Formation documents signed",
          "Beneficial ownership attested",
        ].map((item, i) => (
          <div
            key={i}
            className="flex items-center gap-3 rounded-lg border border-stone-800/40 bg-stone-900/20 px-4 py-3"
          >
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" strokeWidth={1.5} />
            <span className="text-sm text-stone-400">{item}</span>
          </div>
        ))}
      </motion.div>

      {/* Actions */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: "easeOut", delay: 0.55 }}
        className="mt-10 flex flex-col items-center gap-4"
      >
        <p className="text-sm text-stone-500">
          You can safely close this window, or return to your dashboard.
        </p>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 rounded-lg bg-bronze-500 px-6 py-2.5 text-sm font-semibold text-stone-950 transition-all duration-200 hover:bg-bronze-400 hover:shadow-lg hover:shadow-bronze-500/10"
        >
          Return to Dashboard
          <ArrowRight className="h-4 w-4" />
        </Link>
      </motion.div>
    </motion.div>
  );
}
