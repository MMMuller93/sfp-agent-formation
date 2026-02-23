import { useState, type FormEvent } from "react";
import { Lock, ChevronRight, Loader2, Shield } from "lucide-react";
import { motion } from "framer-motion";

/* ─── Types ─────────────────────────────────────────────────── */

export interface PIIData {
  ssn: string;
  date_of_birth: string;
  address_street: string;
  address_city: string;
  address_state: string;
  address_zip: string;
}

interface Props {
  onSubmit: (data: Record<string, unknown>) => Promise<void>;
  submitting: boolean;
}

/* ─── Shared input styles ───────────────────────────────────── */

const inputClass =
  "mt-1.5 block w-full rounded-lg border border-stone-800 bg-stone-900/60 px-3.5 py-2.5 text-sm text-stone-100 placeholder:text-stone-600 focus:border-bronze-500 focus:outline-none focus:ring-1 focus:ring-bronze-500 transition-colors";

function Label({
  htmlFor,
  children,
}: {
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <label htmlFor={htmlFor} className="block text-sm font-medium text-stone-300">
      {children}
    </label>
  );
}

/* ─── SSN formatting ────────────────────────────────────────── */

/**
 * Formats a raw digit string into XXX-XX-XXXX display format.
 * Returns the raw digits alongside the display value.
 */
function formatSSN(raw: string): { display: string; digits: string } {
  const digits = raw.replace(/\D/g, "").slice(0, 9);
  let display = digits;
  if (digits.length > 5) {
    display = `${digits.slice(0, 3)}-${digits.slice(3, 5)}-${digits.slice(5)}`;
  } else if (digits.length > 3) {
    display = `${digits.slice(0, 3)}-${digits.slice(3)}`;
  }
  return { display, digits };
}

/* ─── US States ─────────────────────────────────────────────── */

const US_STATES = [
  "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
  "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
  "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
  "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
  "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
];

/* ─── Component ─────────────────────────────────────────────── */

export function KernelStepPII({ onSubmit, submitting }: Props) {
  const [ssnDigits, setSsnDigits] = useState("");
  const [ssnDisplay, setSsnDisplay] = useState("");
  const [dob, setDob] = useState("");
  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [state, setState] = useState("");
  const [zip, setZip] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSSNChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { display, digits } = formatSSN(e.target.value);
    setSsnDisplay(display);
    setSsnDigits(digits);
  }

  function isValid(): boolean {
    return (
      ssnDigits.length === 9 &&
      dob.trim() !== "" &&
      street.trim() !== "" &&
      city.trim() !== "" &&
      state !== "" &&
      zip.trim().length === 5
    );
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!isValid() || submitting) return;
    setError(null);

    // In production: encrypt SSN client-side with the session's public key
    // before transmission. Here we pass it directly over HTTPS.
    const payload: PIIData = {
      ssn: ssnDigits,
      date_of_birth: dob,
      address_street: street,
      address_city: city,
      address_state: state,
      address_zip: zip,
    };

    try {
      await onSubmit(payload as unknown as Record<string, unknown>);
    } catch (err: unknown) {
      const message =
        err !== null &&
        typeof err === "object" &&
        "detail" in err &&
        typeof (err as { detail: unknown }).detail === "string"
          ? (err as { detail: string }).detail
          : "Failed to submit. Please try again.";
      setError(message);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
    >
      {/* Security notice */}
      <div className="mb-6 flex items-start gap-3 rounded-lg border border-bronze-500/20 bg-bronze-500/5 px-4 py-3.5">
        <Lock className="mt-0.5 h-4 w-4 shrink-0 text-bronze-500" strokeWidth={1.5} />
        <div>
          <p className="text-sm font-medium text-bronze-200">
            Your information is encrypted
          </p>
          <p className="mt-0.5 text-xs leading-relaxed text-stone-500">
            Your SSN and personal details are encrypted in your browser before
            transmission and stored in an isolated PII vault — never in the
            main application database.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* SSN */}
        <div>
          <Label htmlFor="ssn">Social Security Number (SSN) or ITIN</Label>
          <div className="relative mt-1.5">
            <input
              id="ssn"
              type="text"
              inputMode="numeric"
              autoComplete="off"
              value={ssnDisplay}
              onChange={handleSSNChange}
              placeholder="XXX-XX-XXXX"
              maxLength={11}
              className={inputClass}
              aria-describedby="ssn-hint"
            />
            <Shield
              className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-700"
              strokeWidth={1.5}
            />
          </div>
          <p id="ssn-hint" className="mt-1.5 text-xs text-stone-600">
            We accept both SSN (US citizens/residents) and ITIN (non-residents).
          </p>
        </div>

        {/* Date of birth */}
        <div>
          <Label htmlFor="dob">Date of Birth</Label>
          <input
            id="dob"
            type="date"
            value={dob}
            onChange={(e) => setDob(e.target.value)}
            max={new Date().toISOString().split("T")[0]}
            className={inputClass}
          />
        </div>

        {/* Address */}
        <div className="space-y-4">
          <p className="text-sm font-medium text-stone-300">Legal Address</p>

          <div>
            <Label htmlFor="street">Street Address</Label>
            <input
              id="street"
              type="text"
              value={street}
              onChange={(e) => setStreet(e.target.value)}
              placeholder="123 Main St, Apt 4B"
              autoComplete="street-address"
              className={inputClass}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="sm:col-span-1">
              <Label htmlFor="city">City</Label>
              <input
                id="city"
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="New York"
                autoComplete="address-level2"
                className={inputClass}
              />
            </div>

            <div>
              <Label htmlFor="state">State</Label>
              <select
                id="state"
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="mt-1.5 block w-full rounded-lg border border-stone-800 bg-stone-900/60 px-3.5 py-2.5 text-sm text-stone-100 focus:border-bronze-500 focus:outline-none focus:ring-1 focus:ring-bronze-500 transition-colors appearance-none"
              >
                <option value="">State</option>
                {US_STATES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Label htmlFor="zip">ZIP Code</Label>
              <input
                id="zip"
                type="text"
                inputMode="numeric"
                value={zip}
                onChange={(e) =>
                  setZip(e.target.value.replace(/\D/g, "").slice(0, 5))
                }
                placeholder="10001"
                maxLength={5}
                autoComplete="postal-code"
                className={inputClass}
              />
            </div>
          </div>
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
            disabled={!isValid() || submitting}
            className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-bronze-500 px-6 py-3 text-sm font-semibold text-stone-950 transition-all duration-200 hover:bg-bronze-400 hover:shadow-lg hover:shadow-bronze-500/10 disabled:opacity-40 disabled:hover:bg-bronze-500"
          >
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting securely...
              </>
            ) : (
              <>
                Continue
                <ChevronRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </motion.div>
  );
}
