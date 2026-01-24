"use client";

import { apiFetch } from "@/lib/api";
import { RfiCaseSummary } from "@/lib/types";
import { useEffect, useMemo, useState } from "react";

export default function CustomerQueryTrackerPage() {
  const [cases, setCases] = useState<RfiCaseSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const stats = useMemo(() => {
    const total = cases.length;
    const byStatus = cases.reduce<Record<string, number>>((acc, item) => {
      acc[item.status] = (acc[item.status] ?? 0) + 1;
      return acc;
    }, {});
    return {
      total,
      invited: byStatus.INVITED ?? 0,
      inCall: byStatus.IN_CALL ?? 0,
      summarized: byStatus.SUMMARIZED ?? 0,
      delivered: byStatus.DELIVERED ?? 0,
    };
  }, [cases]);

  const statusBadge = (status: RfiCaseSummary["status"]) => {
    const styles: Record<string, string> = {
      DRAFT: "bg-zinc-100 text-zinc-700",
      INVITED: "bg-amber-100 text-amber-700",
      CALL_READY: "bg-blue-100 text-blue-700",
      IN_CALL: "bg-purple-100 text-purple-700",
      SUMMARIZED: "bg-emerald-100 text-emerald-700",
      DELIVERED: "bg-green-100 text-green-700",
      CLOSED: "bg-zinc-200 text-zinc-700",
    };
    return (
      <span
        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
          styles[status] ?? "bg-zinc-100 text-zinc-700"
        }`}
      >
        {status.replace("_", " ")}
      </span>
    );
  };

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
    const interval = setInterval(loadCases, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 text-zinc-900">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <header className="rounded-3xl border border-zinc-200 bg-gradient-to-br from-white via-white to-zinc-100 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Internal
          </p>
          <h1 className="text-2xl font-semibold">Customer Query Tracker</h1>
          <p className="text-sm text-zinc-600">
            Monitor RFIs and status transitions in real time.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">Total cases</p>
              <p className="mt-2 text-2xl font-semibold text-zinc-900">{stats.total}</p>
            </div>
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">Invited</p>
              <p className="mt-2 text-2xl font-semibold text-amber-700">{stats.invited}</p>
            </div>
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">In call</p>
              <p className="mt-2 text-2xl font-semibold text-purple-700">{stats.inCall}</p>
            </div>
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">Summarized</p>
              <p className="mt-2 text-2xl font-semibold text-emerald-700">
                {stats.summarized}
              </p>
            </div>
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">Delivered</p>
              <p className="mt-2 text-2xl font-semibold text-green-700">
                {stats.delivered}
              </p>
            </div>
          </div>
        </header>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold">RFI Table</h2>
              <p className="text-sm text-zinc-600">
                Updated every few seconds to reflect recent activity.
              </p>
            </div>
          </div>
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
                      <td className="px-4 py-3">{statusBadge(item.status)}</td>
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
