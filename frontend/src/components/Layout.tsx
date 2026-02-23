import { Link, Outlet, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Shield } from "lucide-react";

const NAV_LINKS: { label: string; to: string }[] = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "API Docs", to: "/docs" },
  { label: "Ops", to: "/ops" },
];

function NavLink({ label, to }: { label: string; to: string }) {
  const { pathname } = useLocation();
  const isActive = pathname.startsWith(to);

  return (
    <Link
      to={to}
      className={`text-sm transition-colors duration-200 ${
        isActive
          ? "text-bronze-400 font-medium"
          : "text-stone-400 hover:text-stone-200"
      }`}
    >
      {label}
    </Link>
  );
}

function Header() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-stone-800/60 bg-stone-950/80 backdrop-blur-lg">
      <nav className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <Shield
            className="h-5 w-5 text-bronze-500 transition-transform duration-300 group-hover:scale-110"
            strokeWidth={1.5}
          />
          <span className="text-sm font-semibold tracking-wide text-stone-100">
            SFP
          </span>
          <span className="hidden sm:inline text-xs text-stone-500 font-light tracking-widest uppercase ml-1">
            Entity Formation
          </span>
        </Link>

        {/* Links */}
        <div className="flex items-center gap-6">
          {NAV_LINKS.map((link) => (
            <NavLink key={link.to} {...link} />
          ))}
          <Link
            to="/start"
            className="rounded-md bg-bronze-500 px-3.5 py-1.5 text-sm font-medium text-stone-950 transition-colors duration-200 hover:bg-bronze-400"
          >
            Get Started
          </Link>
        </div>
      </nav>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-stone-800/60 bg-stone-950">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <Shield className="h-4 w-4 text-bronze-500" strokeWidth={1.5} />
            <span className="text-sm font-semibold text-stone-300">
              Sovereign Formation Partners
            </span>
          </div>

          {/* Links */}
          <div className="flex gap-6 text-xs text-stone-500">
            <Link to="/docs" className="hover:text-stone-300 transition-colors">
              API Documentation
            </Link>
            <a
              href="mailto:support@sfp.legal"
              className="hover:text-stone-300 transition-colors"
            >
              Contact
            </a>
          </div>
        </div>

        <div className="mt-8 border-t border-stone-800/40 pt-6 text-center text-xs text-stone-600">
          &copy; {new Date().getFullYear()} Sovereign Formation Partners LLC.
          All rights reserved.
        </div>
      </div>
    </footer>
  );
}

/**
 * Shared application layout.
 * Wraps all routes with consistent header/footer chrome and a
 * fade-in transition on route changes.
 */
export function Layout() {
  const { pathname } = useLocation();

  return (
    <div className="flex min-h-dvh flex-col">
      <Header />

      {/* Main content area — offset for fixed header */}
      <motion.main
        key={pathname}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
        className="flex-1 pt-14"
      >
        <Outlet />
      </motion.main>

      <Footer />
    </div>
  );
}
