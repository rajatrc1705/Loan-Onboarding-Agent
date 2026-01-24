export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-50 font-sans text-zinc-900">
      <main className="mx-auto flex w-full max-w-5xl flex-col gap-8 px-6 py-16">
        <header className="rounded-3xl border border-zinc-200 bg-gradient-to-br from-white via-white to-zinc-100 p-8 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Loan Onboarding
          </p>
          <h1 className="mt-2 text-3xl font-semibold text-zinc-900">
            Risk Team Control Tower
          </h1>
          <p className="mt-2 text-base text-zinc-600">
            Centralize clarifications, monitor case progress, and keep customers moving.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <a
              className="inline-flex items-center justify-center rounded-full bg-zinc-900 px-5 py-2 text-sm font-semibold text-white"
              href="/riskdashboard"
            >
              Open Risk Dashboard
            </a>
            <a
              className="inline-flex items-center justify-center rounded-full border border-zinc-200 px-5 py-2 text-sm font-semibold text-zinc-700"
              href="/customerquerytracker"
            >
              View Query Tracker
            </a>
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">Faster reviews</p>
              <p className="mt-2 text-sm text-zinc-700">
                Gather structured responses without back-and-forth.
              </p>
            </div>
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">Live tracking</p>
              <p className="mt-2 text-sm text-zinc-700">
                Monitor status from invite to delivery in one view.
              </p>
            </div>
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">Audit ready</p>
              <p className="mt-2 text-sm text-zinc-700">
                Keep a clear record of questions and answers.
              </p>
            </div>
          </div>
        </header>

      </main>
    </div>
  );
}
