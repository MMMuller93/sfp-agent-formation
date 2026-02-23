import { motion } from "framer-motion";
import { Clock, Mail } from "lucide-react";

/* ─── Component ─────────────────────────────────────────────── */

export function KernelExpired() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className="flex flex-col items-center py-12 text-center"
    >
      {/* Icon */}
      <div className="flex h-20 w-20 items-center justify-center rounded-full border border-yellow-500/30 bg-yellow-500/5">
        <Clock className="h-10 w-10 text-yellow-500" strokeWidth={1.5} />
      </div>

      {/* Message */}
      <div className="mt-8">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-yellow-500">
          Link Expired
        </p>
        <h2 className="heading-display mt-3 text-3xl text-stone-100">
          This verification link has expired
        </h2>
        <p className="mx-auto mt-4 max-w-sm text-sm leading-relaxed text-stone-500">
          Verification links are single-use and expire for security reasons.
          Please contact your agent or the formation team to receive a new link.
        </p>
      </div>

      {/* Contact option */}
      <div className="mt-10 w-full max-w-sm rounded-xl border border-stone-800/60 bg-stone-900/40 p-6">
        <h3 className="text-sm font-semibold text-stone-300">
          Request a new verification link
        </h3>
        <p className="mt-2 text-xs leading-relaxed text-stone-500">
          Reach out to our formation team and we will send you a fresh
          verification link.
        </p>
        <a
          href="mailto:support@sfp.legal?subject=New%20Verification%20Link%20Request"
          className="mt-4 inline-flex items-center gap-2 rounded-lg border border-stone-700 px-4 py-2.5 text-sm font-medium text-stone-300 transition-colors hover:border-stone-600 hover:text-stone-100"
        >
          <Mail className="h-4 w-4" strokeWidth={1.5} />
          Contact Support
        </a>
      </div>
    </motion.div>
  );
}
