"use client";

export default function MarketingPage() {
  return (
    <div className="min-h-screen bg-white text-zinc-900">
      <main className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 py-16">
        <header className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
          <div className="grid gap-5">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-zinc-500">
              Loan Onboarding Control Tower
            </p>
            <h1 className="text-4xl font-semibold leading-tight sm:text-5xl">
              Speed up lending decisions with a unified RFI + risk workflow.
            </h1>
            <p className="text-lg text-zinc-600">
              Automate clarifications, capture structured borrower responses, and
              keep underwriting teams aligned in one shared workspace.
            </p>
            <div className="flex flex-wrap gap-3">
              <button className="rounded-full bg-zinc-900 px-6 py-3 text-sm font-semibold text-white">
                Request a demo
              </button>
              <button className="rounded-full border border-zinc-200 px-6 py-3 text-sm font-semibold text-zinc-700">
                See a walkthrough
              </button>
            </div>
            <div className="flex flex-wrap gap-6 text-sm text-zinc-500">
              <span>Live status tracking</span>
              <span>Automated follow-ups</span>
              <span>Audit-ready records</span>
            </div>
          </div>
          <div className="rounded-3xl border border-zinc-200 bg-zinc-50 p-6 shadow-sm">
            <div className="flex items-center justify-between text-xs font-semibold uppercase text-zinc-500">
              <span>Live risk overview</span>
              <span>Updated seconds ago</span>
            </div>
            <div className="mt-4 grid gap-4">
              <div className="rounded-2xl border border-zinc-200 bg-white p-4">
                <p className="text-xs font-semibold uppercase text-zinc-500">
                  Total cases
                </p>
                <p className="mt-2 text-2xl font-semibold">128</p>
                <p className="mt-1 text-sm text-zinc-500">
                  22 awaiting borrower response
                </p>
              </div>
              <div className="rounded-2xl border border-zinc-200 bg-white p-4">
                <p className="text-xs font-semibold uppercase text-zinc-500">
                  Invitations sent
                </p>
                <p className="mt-2 text-2xl font-semibold">47</p>
                <p className="mt-1 text-sm text-zinc-500">
                  9 links expiring in 48 hours
                </p>
              </div>
              <div className="rounded-2xl border border-zinc-200 bg-white p-4">
                <p className="text-xs font-semibold uppercase text-zinc-500">
                  Call-ready
                </p>
                <p className="mt-2 text-2xl font-semibold">13</p>
                <p className="mt-1 text-sm text-zinc-500">
                  Auto-routing to agents enabled
                </p>
              </div>
            </div>
          </div>
        </header>

        <section className="grid gap-6 lg:grid-cols-3">
          {[
            {
              title: "Smart RFI intake",
              body:
                "Generate structured question sets, reuse templates, and capture answers in real time.",
            },
            {
              title: "Risk-ready timelines",
              body:
                "Track borrower responsiveness with audit-ready timestamps and clear ownership.",
            },
            {
              title: "Ops command center",
              body:
                "One dashboard to triage cases, assign agents, and prevent stalled applications.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-3xl border border-zinc-200 bg-white p-6 shadow-sm"
            >
              <h3 className="text-lg font-semibold">{item.title}</h3>
              <p className="mt-3 text-sm text-zinc-600">{item.body}</p>
            </div>
          ))}
        </section>

        <section className="rounded-3xl border border-zinc-200 bg-gradient-to-br from-zinc-900 via-zinc-900 to-zinc-800 p-10 text-white">
          <div className="grid gap-5">
            <h2 className="text-3xl font-semibold">
              Ready to shorten your risk review cycle?
            </h2>
            <p className="text-base text-zinc-200">
              Share a single link with borrowers, keep the full audit trail, and
              sync every stakeholder in minutes.
            </p>
            <div className="flex flex-wrap gap-3">
              <button className="rounded-full bg-white px-6 py-3 text-sm font-semibold text-zinc-900">
                Book a demo
              </button>
              <button className="rounded-full border border-white/40 px-6 py-3 text-sm font-semibold text-white">
                Download PDF
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
