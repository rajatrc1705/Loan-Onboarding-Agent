export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-50 font-sans text-zinc-900">
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-8 px-6 py-16">
        <div className="flex flex-col gap-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Onboarding Control Tower
          </p>
          <h1 className="text-3xl font-semibold text-zinc-900">
            Clarification RFI MVP
          </h1>
          <p className="text-base text-zinc-600">
            Internal dashboards, customer magic links, and LiveKit calls.
          </p>
        </div>

        <div className="grid gap-4 rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Quick Links</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <a className="rounded-lg border border-zinc-200 p-4 hover:border-zinc-300" href="/riskdashboard">
              <p className="font-semibold">Risk Dashboard</p>
              <p className="text-sm text-zinc-600">Create RFIs and send invites.</p>
            </a>
            <a className="rounded-lg border border-zinc-200 p-4 hover:border-zinc-300" href="/customerquerytracker">
              <p className="font-semibold">Customer Query Tracker</p>
              <p className="text-sm text-zinc-600">Track open cases and status.</p>
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
