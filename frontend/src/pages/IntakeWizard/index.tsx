import { useState, type FormEvent, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  User,
  Bot,
  FileCheck,
  ChevronRight,
  ChevronLeft,
  MapPin,
  Plus,
  Trash2,
  Loader2,
} from "lucide-react";
import { api } from "@/lib/api";

/* ─── Constants ─────────────────────────────────────────────── */

const STEPS = [
  { id: "jurisdiction", label: "Jurisdiction", icon: MapPin },
  { id: "entity", label: "Entity Details", icon: Building2 },
  { id: "members", label: "Members", icon: User },
  { id: "agent", label: "AI Agent", icon: Bot },
  { id: "review", label: "Review", icon: FileCheck },
] as const;

const JURISDICTIONS = [
  {
    code: "DE" as const,
    name: "Delaware",
    description:
      "Most popular for LLCs. Strong legal precedent, business-friendly courts.",
    pricing: { llc: "$499", corporation: "$599" },
  },
  {
    code: "WY" as const,
    name: "Wyoming",
    description:
      "Best for DAO LLCs. Recognizes smart contract governance.",
    pricing: { llc: "$499", dao_llc: "$699" },
  },
];

type JurisdictionCode = "DE" | "WY";

interface VehicleOption {
  value: string;
  label: string;
  description: string;
}

const VEHICLE_TYPES: Record<JurisdictionCode, VehicleOption[]> = {
  DE: [
    { value: "llc", label: "LLC", description: "Standard limited liability company" },
    {
      value: "corporation",
      label: "Corporation",
      description: "C-Corp or S-Corp",
    },
  ],
  WY: [
    { value: "llc", label: "LLC", description: "Standard limited liability company" },
    {
      value: "dao_llc",
      label: "DAO LLC",
      description: "Decentralized autonomous organization",
    },
  ],
};

/* ─── Types ─────────────────────────────────────────────────── */

interface Member {
  legal_name: string;
  email: string;
  role: string;
  ownership_percentage: number;
}

interface AgentConfig {
  enabled: boolean;
  display_name: string;
  authority_scope: Record<string, boolean>;
  transaction_limit_cents: number;
}

interface FormData {
  jurisdiction: JurisdictionCode | "";
  vehicle_type: string;
  requested_name: string;
  members: Member[];
  agent: AgentConfig;
}

const INITIAL_MEMBER: Member = {
  legal_name: "",
  email: "",
  role: "member",
  ownership_percentage: 100,
};

const INITIAL_AGENT: AgentConfig = {
  enabled: false,
  display_name: "",
  authority_scope: {
    sign_documents: false,
    manage_compliance: false,
    execute_transactions: false,
  },
  transaction_limit_cents: 0,
};

const INITIAL_FORM: FormData = {
  jurisdiction: "",
  vehicle_type: "",
  requested_name: "",
  members: [{ ...INITIAL_MEMBER }],
  agent: { ...INITIAL_AGENT },
};

/* ─── Animation variants ────────────────────────────────────── */

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 80 : -80,
    opacity: 0,
  }),
  center: { x: 0, opacity: 1 },
  exit: (direction: number) => ({
    x: direction > 0 ? -80 : 80,
    opacity: 0,
  }),
};

/* ─── Shared UI helpers ─────────────────────────────────────── */

function StepCard({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto max-w-2xl rounded-xl border border-stone-800/60 bg-stone-900/40 p-8">
      {children}
    </div>
  );
}

function Label({
  htmlFor,
  children,
}: {
  htmlFor: string;
  children: ReactNode;
}) {
  return (
    <label
      htmlFor={htmlFor}
      className="block text-sm font-medium text-stone-300"
    >
      {children}
    </label>
  );
}

const inputClass =
  "mt-1.5 block w-full rounded-lg border border-stone-800 bg-stone-900/60 px-3.5 py-2.5 text-sm text-stone-100 placeholder:text-stone-600 focus:border-bronze-500 focus:outline-none focus:ring-1 focus:ring-bronze-500 transition-colors";

const selectClass =
  "mt-1.5 block w-full rounded-lg border border-stone-800 bg-stone-900/60 px-3.5 py-2.5 text-sm text-stone-100 focus:border-bronze-500 focus:outline-none focus:ring-1 focus:ring-bronze-500 transition-colors appearance-none";

/* ─── Step 1: Jurisdiction ──────────────────────────────────── */

function JurisdictionStep({
  value,
  onChange,
}: {
  value: FormData["jurisdiction"];
  onChange: (code: JurisdictionCode) => void;
}) {
  return (
    <StepCard>
      <h2 className="heading-display text-2xl text-stone-100">
        Choose Jurisdiction
      </h2>
      <p className="mt-2 text-sm text-stone-500">
        Select where you want your entity formed.
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {JURISDICTIONS.map((j) => {
          const selected = value === j.code;
          return (
            <button
              key={j.code}
              type="button"
              onClick={() => onChange(j.code)}
              className={`rounded-lg border p-5 text-left transition-all duration-200 ${
                selected
                  ? "border-bronze-500 bg-bronze-500/5 ring-1 ring-bronze-500/30"
                  : "border-stone-800 bg-stone-900/30 hover:border-stone-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-lg font-semibold text-stone-100">
                  {j.name}
                </span>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    selected
                      ? "bg-bronze-500/20 text-bronze-400"
                      : "bg-stone-800 text-stone-500"
                  }`}
                >
                  {j.code}
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-stone-500">
                {j.description}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {Object.entries(j.pricing).map(([type, price]) => (
                  <span
                    key={type}
                    className="rounded-md bg-stone-800/60 px-2 py-1 text-xs text-stone-400"
                  >
                    {type.replace("_", " ").toUpperCase()}: {price}
                  </span>
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </StepCard>
  );
}

/* ─── Step 2: Entity Details ────────────────────────────────── */

function EntityStep({
  form,
  onUpdate,
}: {
  form: FormData;
  onUpdate: (patch: Partial<FormData>) => void;
}) {
  const jurisdiction = form.jurisdiction as JurisdictionCode;
  const vehicles = jurisdiction ? VEHICLE_TYPES[jurisdiction] : [];

  return (
    <StepCard>
      <h2 className="heading-display text-2xl text-stone-100">
        Entity Details
      </h2>
      <p className="mt-2 text-sm text-stone-500">
        Name your entity and choose a vehicle type.
      </p>

      <div className="mt-8 space-y-6">
        <div>
          <Label htmlFor="entity-name">Entity Name</Label>
          <input
            id="entity-name"
            type="text"
            value={form.requested_name}
            onChange={(e) => onUpdate({ requested_name: e.target.value })}
            placeholder="e.g. Nexus Autonomous Holdings LLC"
            className={inputClass}
          />
          <p className="mt-1.5 text-xs text-stone-600">
            Include the entity suffix (LLC, Inc, etc.)
          </p>
        </div>

        <div>
          <Label htmlFor="vehicle-type">Vehicle Type</Label>
          <select
            id="vehicle-type"
            value={form.vehicle_type}
            onChange={(e) => onUpdate({ vehicle_type: e.target.value })}
            className={selectClass}
          >
            <option value="">Select a type...</option>
            {vehicles.map((v) => (
              <option key={v.value} value={v.value}>
                {v.label} — {v.description}
              </option>
            ))}
          </select>
        </div>
      </div>
    </StepCard>
  );
}

/* ─── Step 3: Members ───────────────────────────────────────── */

function MembersStep({
  members,
  onUpdate,
}: {
  members: Member[];
  onUpdate: (members: Member[]) => void;
}) {
  function updateMember(index: number, patch: Partial<Member>) {
    const updated = members.map((m, i) =>
      i === index ? { ...m, ...patch } : m,
    );
    onUpdate(updated);
  }

  function addMember() {
    onUpdate([
      ...members,
      { ...INITIAL_MEMBER, ownership_percentage: 0 },
    ]);
  }

  function removeMember(index: number) {
    if (members.length <= 1) return;
    onUpdate(members.filter((_, i) => i !== index));
  }

  const totalOwnership = members.reduce(
    (sum, m) => sum + m.ownership_percentage,
    0,
  );

  return (
    <StepCard>
      <h2 className="heading-display text-2xl text-stone-100">
        Member Information
      </h2>
      <p className="mt-2 text-sm text-stone-500">
        Add the members or beneficial owners of your entity.
      </p>

      <div className="mt-8 space-y-6">
        {members.map((member, index) => (
          <div
            key={index}
            className="rounded-lg border border-stone-800/40 bg-stone-900/20 p-5"
          >
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-stone-400">
                Member {index + 1}
              </span>
              {members.length > 1 && (
                <button
                  type="button"
                  onClick={() => removeMember(index)}
                  className="rounded-md p-1.5 text-stone-600 transition-colors hover:bg-stone-800 hover:text-red-400"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor={`member-name-${index}`}>Legal Name</Label>
                <input
                  id={`member-name-${index}`}
                  type="text"
                  value={member.legal_name}
                  onChange={(e) =>
                    updateMember(index, { legal_name: e.target.value })
                  }
                  placeholder="Full legal name"
                  className={inputClass}
                />
              </div>
              <div>
                <Label htmlFor={`member-email-${index}`}>Email</Label>
                <input
                  id={`member-email-${index}`}
                  type="email"
                  value={member.email}
                  onChange={(e) =>
                    updateMember(index, { email: e.target.value })
                  }
                  placeholder="email@example.com"
                  className={inputClass}
                />
              </div>
              <div>
                <Label htmlFor={`member-role-${index}`}>Role</Label>
                <select
                  id={`member-role-${index}`}
                  value={member.role}
                  onChange={(e) =>
                    updateMember(index, { role: e.target.value })
                  }
                  className={selectClass}
                >
                  <option value="member">Member</option>
                  <option value="manager">Manager</option>
                  <option value="organizer">Organizer</option>
                </select>
              </div>
              <div>
                <Label htmlFor={`member-ownership-${index}`}>
                  Ownership %
                </Label>
                <input
                  id={`member-ownership-${index}`}
                  type="number"
                  min={0}
                  max={100}
                  value={member.ownership_percentage}
                  onChange={(e) =>
                    updateMember(index, {
                      ownership_percentage: Number(e.target.value),
                    })
                  }
                  className={inputClass}
                />
              </div>
            </div>
          </div>
        ))}

        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={addMember}
            className="inline-flex items-center gap-1.5 rounded-lg border border-stone-700 px-3.5 py-2 text-sm text-stone-300 transition-colors hover:border-stone-600 hover:text-stone-100"
          >
            <Plus className="h-4 w-4" />
            Add Member
          </button>

          <span
            className={`text-sm font-medium ${
              totalOwnership === 100
                ? "text-emerald-400"
                : "text-yellow-400"
            }`}
          >
            Total: {totalOwnership}%
          </span>
        </div>
      </div>
    </StepCard>
  );
}

/* ─── Step 4: Agent Configuration ───────────────────────────── */

function AgentStep({
  agent,
  onUpdate,
}: {
  agent: AgentConfig;
  onUpdate: (agent: AgentConfig) => void;
}) {
  function toggleScope(key: string) {
    onUpdate({
      ...agent,
      authority_scope: {
        ...agent.authority_scope,
        [key]: !agent.authority_scope[key],
      },
    });
  }

  const scopeLabels: Record<string, string> = {
    sign_documents: "Sign Documents",
    manage_compliance: "Manage Compliance",
    execute_transactions: "Execute Transactions",
  };

  return (
    <StepCard>
      <h2 className="heading-display text-2xl text-stone-100">
        AI Agent Configuration
      </h2>
      <p className="mt-2 text-sm text-stone-500">
        Optionally attach an AI agent to manage this entity.
      </p>

      <div className="mt-8 space-y-6">
        {/* Enable toggle */}
        <label className="flex cursor-pointer items-center gap-3">
          <div className="relative">
            <input
              type="checkbox"
              checked={agent.enabled}
              onChange={(e) =>
                onUpdate({ ...agent, enabled: e.target.checked })
              }
              className="peer sr-only"
            />
            <div className="h-6 w-11 rounded-full bg-stone-700 transition-colors peer-checked:bg-bronze-500" />
            <div className="absolute left-0.5 top-0.5 h-5 w-5 rounded-full bg-stone-200 transition-transform peer-checked:translate-x-5" />
          </div>
          <span className="text-sm font-medium text-stone-200">
            Enable AI Agent
          </span>
        </label>

        {agent.enabled && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-6"
          >
            <div>
              <Label htmlFor="agent-name">Agent Display Name</Label>
              <input
                id="agent-name"
                type="text"
                value={agent.display_name}
                onChange={(e) =>
                  onUpdate({ ...agent, display_name: e.target.value })
                }
                placeholder="e.g. Nexus Agent"
                className={inputClass}
              />
            </div>

            <div>
              <p className="text-sm font-medium text-stone-300">
                Authority Scope
              </p>
              <div className="mt-3 space-y-3">
                {Object.entries(agent.authority_scope).map(
                  ([key, enabled]) => (
                    <label
                      key={key}
                      className="flex cursor-pointer items-center gap-3"
                    >
                      <input
                        type="checkbox"
                        checked={enabled}
                        onChange={() => toggleScope(key)}
                        className="h-4 w-4 rounded border-stone-700 bg-stone-900 text-bronze-500 focus:ring-bronze-500 focus:ring-offset-0"
                      />
                      <span className="text-sm text-stone-300">
                        {scopeLabels[key] ?? key}
                      </span>
                    </label>
                  ),
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="tx-limit">
                Transaction Limit (USD)
              </Label>
              <input
                id="tx-limit"
                type="number"
                min={0}
                step={100}
                value={agent.transaction_limit_cents / 100}
                onChange={(e) =>
                  onUpdate({
                    ...agent,
                    transaction_limit_cents:
                      Math.round(Number(e.target.value) * 100),
                  })
                }
                placeholder="0"
                className={inputClass}
              />
              <p className="mt-1.5 text-xs text-stone-600">
                Maximum per-transaction amount the agent can authorize.
                Set to 0 for no limit.
              </p>
            </div>
          </motion.div>
        )}
      </div>
    </StepCard>
  );
}

/* ─── Step 5: Review ────────────────────────────────────────── */

function ReviewRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-baseline justify-between border-b border-stone-800/40 py-3">
      <span className="text-sm text-stone-500">{label}</span>
      <span className="text-sm font-medium text-stone-200">{value}</span>
    </div>
  );
}

function ReviewStep({ form }: { form: FormData }) {
  const jurisdictionName =
    JURISDICTIONS.find((j) => j.code === form.jurisdiction)?.name ??
    form.jurisdiction;

  return (
    <StepCard>
      <h2 className="heading-display text-2xl text-stone-100">
        Review Your Order
      </h2>
      <p className="mt-2 text-sm text-stone-500">
        Confirm the details below before submitting.
      </p>

      <div className="mt-8 space-y-1">
        <ReviewRow label="Jurisdiction" value={jurisdictionName} />
        <ReviewRow label="Entity Name" value={form.requested_name} />
        <ReviewRow
          label="Vehicle Type"
          value={form.vehicle_type.replace("_", " ").toUpperCase()}
        />
      </div>

      {/* Members */}
      <div className="mt-8">
        <h3 className="text-sm font-semibold text-stone-300">Members</h3>
        <div className="mt-3 space-y-2">
          {form.members.map((m, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded-lg border border-stone-800/40 bg-stone-900/20 px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-stone-200">
                  {m.legal_name || "Unnamed"}
                </p>
                <p className="text-xs text-stone-500">
                  {m.email} &middot; {m.role}
                </p>
              </div>
              <span className="text-sm font-medium text-bronze-400">
                {m.ownership_percentage}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Agent */}
      {form.agent.enabled && (
        <div className="mt-8">
          <h3 className="text-sm font-semibold text-stone-300">
            AI Agent
          </h3>
          <div className="mt-3 space-y-1">
            <ReviewRow
              label="Display Name"
              value={form.agent.display_name || "Not set"}
            />
            <ReviewRow
              label="Authority"
              value={
                Object.entries(form.agent.authority_scope)
                  .filter(([, v]) => v)
                  .map(([k]) => k.replace(/_/g, " "))
                  .join(", ") || "None"
              }
            />
            <ReviewRow
              label="Transaction Limit"
              value={
                form.agent.transaction_limit_cents > 0
                  ? `$${(form.agent.transaction_limit_cents / 100).toLocaleString()}`
                  : "No limit"
              }
            />
          </div>
        </div>
      )}
    </StepCard>
  );
}

/* ─── Progress Indicator ────────────────────────────────────── */

function ProgressBar({ currentStep }: { currentStep: number }) {
  return (
    <div className="mx-auto mb-10 flex max-w-2xl items-center justify-between">
      {STEPS.map((step, index) => {
        const Icon = step.icon;
        const isComplete = index < currentStep;
        const isActive = index === currentStep;

        return (
          <div key={step.id} className="flex items-center">
            {/* Connector line */}
            {index > 0 && (
              <div
                className={`mx-2 hidden h-px w-8 sm:block md:w-12 lg:w-16 ${
                  isComplete ? "bg-bronze-500" : "bg-stone-800"
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

/* ─── Validation ────────────────────────────────────────────── */

function isStepValid(currentStep: number, form: FormData): boolean {
  switch (currentStep) {
    case 0:
      return form.jurisdiction !== "";
    case 1:
      return form.requested_name.trim() !== "" && form.vehicle_type !== "";
    case 2:
      return (
        form.members.length > 0 &&
        form.members.every(
          (m) =>
            m.legal_name.trim() !== "" &&
            m.email.trim() !== "" &&
            m.ownership_percentage > 0,
        )
      );
    case 3:
      // Agent step is optional — always valid
      return true;
    case 4:
      return true;
    default:
      return false;
  }
}

/* ─── Main Wizard ───────────────────────────────────────────── */

export function IntakeWizard() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [direction, setDirection] = useState(1);
  const [form, setForm] = useState<FormData>({ ...INITIAL_FORM });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateForm(patch: Partial<FormData>) {
    setForm((prev) => ({ ...prev, ...patch }));
  }

  function goNext() {
    if (!isStepValid(step, form)) return;
    setDirection(1);
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function goBack() {
    setDirection(-1);
    setStep((s) => Math.max(s - 1, 0));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (submitting) return;
    setError(null);
    setSubmitting(true);

    try {
      const order = await api.orders.create({
        requested_name: form.requested_name,
        jurisdiction: form.jurisdiction as "DE" | "WY",
        vehicle_type: form.vehicle_type as "llc" | "dao_llc" | "corporation",
        members: form.members.map((m) => ({
          legal_name: m.legal_name,
          email: m.email || null,
          role: m.role as "member" | "manager" | "registered_agent" | "responsible_party",
          ownership_percentage: m.ownership_percentage,
        })),
        agent: form.agent.enabled
          ? {
              display_name: form.agent.display_name,
              authority_scope: form.agent.authority_scope,
              transaction_limit_cents:
                form.agent.transaction_limit_cents > 0
                  ? form.agent.transaction_limit_cents
                  : null,
            }
          : null,
      });

      navigate(`/dashboard/${order.id}`);
    } catch (err: unknown) {
      const message =
        err !== null &&
        typeof err === "object" &&
        "detail" in err &&
        typeof (err as { detail: unknown }).detail === "string"
          ? (err as { detail: string }).detail
          : "Failed to create order. Please try again.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  const canProceed = isStepValid(step, form);
  const isLastStep = step === STEPS.length - 1;

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
        <div className="mb-8 text-center">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-bronze-500">
            Entity Formation
          </p>
          <h1 className="heading-display mt-2 text-3xl text-stone-100">
            Create Your Entity
          </h1>
        </div>

        {/* Progress */}
        <ProgressBar currentStep={step} />

        {/* Step content */}
        <form onSubmit={handleSubmit}>
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={step}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.25, ease: "easeInOut" }}
            >
              {step === 0 && (
                <JurisdictionStep
                  value={form.jurisdiction}
                  onChange={(code) =>
                    updateForm({ jurisdiction: code, vehicle_type: "" })
                  }
                />
              )}
              {step === 1 && (
                <EntityStep form={form} onUpdate={updateForm} />
              )}
              {step === 2 && (
                <MembersStep
                  members={form.members}
                  onUpdate={(members) => updateForm({ members })}
                />
              )}
              {step === 3 && (
                <AgentStep
                  agent={form.agent}
                  onUpdate={(agent) => updateForm({ agent })}
                />
              )}
              {step === 4 && <ReviewStep form={form} />}
            </motion.div>
          </AnimatePresence>

          {/* Error message */}
          {error && (
            <div className="mx-auto mt-4 max-w-2xl rounded-lg border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Navigation buttons */}
          <div className="mx-auto mt-8 flex max-w-2xl items-center justify-between">
            <button
              type="button"
              onClick={goBack}
              disabled={step === 0}
              className="inline-flex items-center gap-1.5 rounded-lg border border-stone-700 px-5 py-2.5 text-sm font-medium text-stone-300 transition-colors hover:border-stone-600 hover:text-stone-100 disabled:pointer-events-none disabled:opacity-30"
            >
              <ChevronLeft className="h-4 w-4" />
              Back
            </button>

            {isLastStep ? (
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center gap-2 rounded-lg bg-bronze-500 px-6 py-2.5 text-sm font-semibold text-stone-950 transition-all duration-200 hover:bg-bronze-400 hover:shadow-lg hover:shadow-bronze-500/10 disabled:opacity-60"
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    Create Order
                    <ChevronRight className="h-4 w-4" />
                  </>
                )}
              </button>
            ) : (
              <button
                type="button"
                onClick={goNext}
                disabled={!canProceed}
                className="inline-flex items-center gap-1.5 rounded-lg bg-bronze-500 px-5 py-2.5 text-sm font-semibold text-stone-950 transition-all duration-200 hover:bg-bronze-400 disabled:opacity-40 disabled:hover:bg-bronze-500"
              >
                Continue
                <ChevronRight className="h-4 w-4" />
              </button>
            )}
          </div>
        </form>
      </div>
    </section>
  );
}
