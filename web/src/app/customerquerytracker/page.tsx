"use client";

import { apiFetch } from "@/lib/api";
import { RfiCaseSummary } from "@/lib/types";
import { useEffect, useState } from "react";

export default function CustomerQueryTrackerPage() {
  const [cases, setCases] = useState<RfiCaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadCases = async () => {
      try {
        const response = await apiFetch<RfiCaseSummary[]>("/rfi");
        setCases(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load cases");
      }
    };
    loadCases();
  }, []);

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 text-zinc-900">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <header className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Internal
          </p>
          <h1 className="text-2xl font-semibold">Customer Query Tracker</h1>
          <p className="text-sm text-zinc-600">
            Monitor RFIs and status transitions in real time.
          </p>
        </header>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">RFI Table</h2>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          <div className="mt-4 overflow-hidden rounded-lg border border-zinc-200">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-100 text-xs uppercase text-zinc-500">
                <tr>
                  <th className="px-4 py-2">Customer</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">Updated</th>
                  <th className="px-4 py-2">Open</th>
                </tr>
              </thead>
              <tbody>
                {cases.length === 0 ? (
                  <tr>
                    <td className="px-4 py-3 text-sm text-zinc-500" colSpan={4}>
                      No RFIs yet.
                    </td>
                  </tr>
                ) : (
                  cases.map((item) => (
                    <tr key={item.id} className="border-t border-zinc-200">
                      <td className="px-4 py-3">{item.customer_email}</td>
                      <td className="px-4 py-3">{item.status}</td>
                      <td className="px-4 py-3">
                        {new Date(item.updated_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        <a className="underline" href={`/rfi/${item.id}`}>
                          View
                        </a>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
