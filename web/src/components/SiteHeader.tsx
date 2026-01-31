"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navLinks = [
  { href: "/", label: "Home" },
  { href: "/riskdashboard", label: "Risk Dashboard" },
  { href: "/customerquerytracker", label: "Query Tracker" },
];

export default function SiteHeader() {
  const pathname = usePathname();
  if (pathname?.startsWith("/c/")) {
    return null;
  }

  return (
    <header className="sticky top-0 z-50 border-b border-zinc-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Loan Onboarding
          </span>
        </div>
        <nav className="flex flex-wrap items-center gap-2 text-sm font-semibold text-zinc-700">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-full px-3 py-1 ${
                  isActive
                    ? "bg-zinc-900 text-white"
                    : "border border-zinc-200 text-zinc-700 hover:border-zinc-300"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
