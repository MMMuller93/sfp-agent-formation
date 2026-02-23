import { Link } from "react-router-dom";
import { motion, useInView } from "framer-motion";
import {
  FileText,
  UserCheck,
  Building2,
  CheckCircle2,
  ArrowRight,
  Shield,
  Zap,
  Globe,
  Code2,
  Check,
} from "lucide-react";
import { useRef, type ReactNode } from "react";

/* ─── Animation helpers ─────────────────────────────────────── */

function FadeIn({
  children,
  className = "",
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 24 }}
      animate={inView ? { opacity: 1, y: 0 } : undefined}
      transition={{ duration: 0.5, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

/* ─── Hero ──────────────────────────────────────────────────── */

function Hero() {
  return (
    <section className="relative overflow-hidden">
      {/* Background gradient */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% -10%, rgba(191,159,117,0.08) 0%, transparent 60%)",
        }}
      />

      <div className="relative mx-auto max-w-6xl px-6 pb-24 pt-32 sm:pt-40">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="max-w-3xl"
        >
          <p className="text-sm font-medium uppercase tracking-[0.2em] text-bronze-500">
            Sovereign Formation Partners
          </p>

          <h1 className="heading-display mt-6 text-4xl leading-[1.1] text-stone-50 sm:text-5xl lg:text-6xl">
            Legal Infrastructure
            <br />
            <span className="text-bronze-400">for AI Agents</span>
          </h1>

          <p className="mt-6 max-w-xl text-lg leading-relaxed text-stone-400">
            Form LLCs programmatically. Your agent sends a single API call
            &mdash; we handle registered agents, state filings, EIN
            applications, and compliance. Real entities, not wrappers.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Link
              to="/start"
              className="group inline-flex items-center gap-2 rounded-lg bg-bronze-500 px-6 py-3 text-sm font-semibold text-stone-950 transition-all duration-200 hover:bg-bronze-400 hover:shadow-lg hover:shadow-bronze-500/10"
            >
              Get Started
              <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
            </Link>
            <Link
              to="/docs"
              className="inline-flex items-center gap-2 rounded-lg border border-stone-700 px-6 py-3 text-sm font-medium text-stone-300 transition-colors duration-200 hover:border-stone-600 hover:text-stone-100"
            >
              Read the Docs
            </Link>
          </div>
        </motion.div>

        {/* Trust indicators */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-16 flex flex-wrap gap-x-8 gap-y-3 text-xs text-stone-500"
        >
          {[
            "Delaware & Wyoming",
            "SOC 2 Compliant",
            "Human-in-the-Loop Verification",
            "48-Hour Formation",
          ].map((item) => (
            <span key={item} className="flex items-center gap-1.5">
              <span className="h-1 w-1 rounded-full bg-bronze-600" />
              {item}
            </span>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

/* ─── How It Works ──────────────────────────────────────────── */

const STEPS: {
  icon: typeof FileText;
  title: string;
  description: string;
}[] = [
  {
    icon: FileText,
    title: "Create Order",
    description:
      "Your agent calls POST /v1/orders with the entity name, jurisdiction, and beneficial owner details.",
  },
  {
    icon: UserCheck,
    title: "Human Verification",
    description:
      "A compliance officer reviews the order via our Human Kernel — ensuring legal and regulatory fitness.",
  },
  {
    icon: Building2,
    title: "State Filing",
    description:
      "We file formation documents with the Secretary of State, obtain the EIN, and appoint a registered agent.",
  },
  {
    icon: CheckCircle2,
    title: "Active Entity",
    description:
      "Your agent receives a webhook with the Certificate of Formation, EIN letter, and operating agreement.",
  },
];

function HowItWorks() {
  return (
    <section className="border-t border-stone-800/50 bg-stone-950">
      <div className="mx-auto max-w-6xl px-6 py-24">
        <FadeIn>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-bronze-500">
            Process
          </p>
          <h2 className="heading-display mt-3 text-3xl text-stone-100 sm:text-4xl">
            How It Works
          </h2>
        </FadeIn>

        <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((step, i) => (
            <FadeIn key={step.title} delay={i * 0.1}>
              <div className="group relative rounded-xl border border-stone-800/60 bg-stone-900/40 p-6 transition-colors duration-300 hover:border-stone-700/80 hover:bg-stone-900/70">
                {/* Step number */}
                <span className="absolute -top-3 left-5 flex h-6 w-6 items-center justify-center rounded-full bg-stone-950 text-[10px] font-semibold text-bronze-500 ring-1 ring-stone-800">
                  {i + 1}
                </span>

                <step.icon
                  className="h-6 w-6 text-bronze-500/80"
                  strokeWidth={1.5}
                />
                <h3 className="mt-4 text-sm font-semibold text-stone-200">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-stone-500">
                  {step.description}
                </p>
              </div>
            </FadeIn>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── For Agents (Code Example) ─────────────────────────────── */

const CODE_SNIPPET = `curl -X POST https://api.sfp.legal/v1/orders \\
  -H "Authorization: Bearer sfp_live_..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "entity_name": "Nexus Autonomous Holdings LLC",
    "jurisdiction": "DE",
    "beneficial_owners": [
      {
        "name": "Operator Corp Inc.",
        "address": "251 Little Falls Dr, Wilmington, DE 19808",
        "ownership_pct": 100
      }
    ],
    "agent_callback_url": "https://your-agent.ai/webhook/formation"
  }'`;

function ForAgents() {
  return (
    <section className="border-t border-stone-800/50">
      <div className="mx-auto max-w-6xl px-6 py-24">
        <div className="grid items-center gap-12 lg:grid-cols-2">
          {/* Copy */}
          <FadeIn>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-bronze-500">
              Built for Machines
            </p>
            <h2 className="heading-display mt-3 text-3xl text-stone-100 sm:text-4xl">
              One API Call.
              <br />
              Real Legal Entity.
            </h2>
            <p className="mt-4 max-w-md text-sm leading-relaxed text-stone-400">
              No web forms. No PDFs. No phone calls. Your agent sends JSON,
              and receives a fully formed LLC with all state and federal
              registrations complete.
            </p>

            <div className="mt-8 space-y-3">
              {[
                { icon: Zap, text: "Sub-second order creation" },
                { icon: Shield, text: "Human-verified compliance layer" },
                { icon: Globe, text: "Webhook delivery on status changes" },
                { icon: Code2, text: "OpenAPI 3.1 schema + MCP server" },
              ].map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-3 text-sm text-stone-300">
                  <Icon className="h-4 w-4 shrink-0 text-bronze-500/70" strokeWidth={1.5} />
                  {text}
                </div>
              ))}
            </div>
          </FadeIn>

          {/* Code block */}
          <FadeIn delay={0.15}>
            <div className="overflow-hidden rounded-xl border border-stone-800/60 bg-stone-900/50">
              {/* Tab bar */}
              <div className="flex items-center gap-2 border-b border-stone-800/40 px-4 py-2.5">
                <span className="h-2.5 w-2.5 rounded-full bg-stone-700" />
                <span className="h-2.5 w-2.5 rounded-full bg-stone-700" />
                <span className="h-2.5 w-2.5 rounded-full bg-stone-700" />
                <span className="ml-3 text-xs text-stone-500">
                  create-entity.sh
                </span>
              </div>
              {/* Code */}
              <pre className="overflow-x-auto p-5">
                <code className="text-[13px] leading-relaxed text-stone-300">
                  {CODE_SNIPPET}
                </code>
              </pre>
            </div>
          </FadeIn>
        </div>
      </div>
    </section>
  );
}

/* ─── Pricing ───────────────────────────────────────────────── */

interface PlanProps {
  name: string;
  price: string;
  jurisdiction: string;
  features: string[];
  highlighted?: boolean;
  delay?: number;
}

function PlanCard({
  name,
  price,
  jurisdiction,
  features,
  highlighted = false,
  delay = 0,
}: PlanProps) {
  return (
    <FadeIn delay={delay}>
      <div
        className={`relative flex flex-col rounded-xl border p-8 transition-colors duration-300 ${
          highlighted
            ? "border-bronze-500/40 bg-stone-900/70"
            : "border-stone-800/60 bg-stone-900/30 hover:border-stone-700/80"
        }`}
      >
        {highlighted && (
          <span className="absolute -top-3 right-6 rounded-full bg-bronze-500 px-3 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-stone-950">
            Popular
          </span>
        )}

        <p className="text-xs font-medium uppercase tracking-[0.15em] text-stone-500">
          {jurisdiction}
        </p>
        <h3 className="mt-2 text-lg font-semibold text-stone-100">{name}</h3>

        <div className="mt-4 flex items-baseline gap-1">
          <span className="heading-display text-4xl text-stone-50">
            {price}
          </span>
          <span className="text-sm text-stone-500">per entity</span>
        </div>

        <ul className="mt-8 flex-1 space-y-3">
          {features.map((f) => (
            <li key={f} className="flex items-start gap-2 text-sm text-stone-400">
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-bronze-500/70" strokeWidth={1.5} />
              {f}
            </li>
          ))}
        </ul>

        <Link
          to="/start"
          className={`mt-8 block rounded-lg py-2.5 text-center text-sm font-medium transition-colors duration-200 ${
            highlighted
              ? "bg-bronze-500 text-stone-950 hover:bg-bronze-400"
              : "border border-stone-700 text-stone-300 hover:border-stone-600 hover:text-stone-100"
          }`}
        >
          Start Formation
        </Link>
      </div>
    </FadeIn>
  );
}

function Pricing() {
  return (
    <section className="border-t border-stone-800/50 bg-stone-950">
      <div className="mx-auto max-w-4xl px-6 py-24">
        <FadeIn>
          <div className="text-center">
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-bronze-500">
              Pricing
            </p>
            <h2 className="heading-display mt-3 text-3xl text-stone-100 sm:text-4xl">
              Transparent, Per-Entity Pricing
            </h2>
            <p className="mt-3 text-sm text-stone-500">
              No subscriptions. No platform fees. Pay only when you form.
            </p>
          </div>
        </FadeIn>

        <div className="mt-14 grid gap-6 sm:grid-cols-2">
          <PlanCard
            name="Delaware LLC"
            price="$299"
            jurisdiction="Delaware"
            features={[
              "Certificate of Formation",
              "Registered agent (1 year)",
              "Operating agreement template",
              "EIN application & letter",
              "Webhook status updates",
              "48-hour formation",
            ]}
            highlighted
            delay={0.05}
          />
          <PlanCard
            name="Wyoming DAO LLC"
            price="$499"
            jurisdiction="Wyoming"
            features={[
              "Everything in Delaware LLC",
              "DAO-optimized operating agreement",
              "Algorithmic governance provisions",
              "Smart contract integration clause",
              "Multi-member support",
              "Annual report filing",
            ]}
            delay={0.15}
          />
        </div>
      </div>
    </section>
  );
}

/* ─── CTA Banner ────────────────────────────────────────────── */

function CtaBanner() {
  return (
    <section className="border-t border-stone-800/50">
      <div className="mx-auto max-w-6xl px-6 py-24">
        <FadeIn>
          <div className="relative overflow-hidden rounded-2xl border border-stone-800/40 bg-stone-900/50 px-8 py-14 text-center sm:px-16">
            {/* Decorative gradient */}
            <div
              aria-hidden
              className="pointer-events-none absolute inset-0"
              style={{
                background:
                  "radial-gradient(ellipse 60% 50% at 50% 100%, rgba(191,159,117,0.06) 0%, transparent 60%)",
              }}
            />

            <h2 className="heading-display relative text-2xl text-stone-100 sm:text-3xl">
              Ready to give your agent a legal identity?
            </h2>
            <p className="relative mt-3 text-sm text-stone-500">
              Formation starts with a single API call. No contracts, no
              minimums.
            </p>
            <Link
              to="/start"
              className="relative mt-8 inline-flex items-center gap-2 rounded-lg bg-bronze-500 px-7 py-3 text-sm font-semibold text-stone-950 transition-colors duration-200 hover:bg-bronze-400"
            >
              Create Your First Entity
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

/* ─── Page Export ────────────────────────────────────────────── */

export function Landing() {
  return (
    <>
      <Hero />
      <HowItWorks />
      <ForAgents />
      <Pricing />
      <CtaBanner />
    </>
  );
}
