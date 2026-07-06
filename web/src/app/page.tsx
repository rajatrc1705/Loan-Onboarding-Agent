"use client";

import { apiFetch } from "@/lib/api";
import { Application, ApplicationList } from "@/lib/types";
import { FormEvent, useEffect, useState } from "react";

export default function Home() {
  const [applications, setApplications] = useState<Application[]>([]);
  const [applicationSearch, setApplicationSearch] = useState("");
  const [submittedApplicationSearch, setSubmittedApplicationSearch] = useState("");
  const [applicationPage, setApplicationPage] = useState(1);
  const [applicationPageSize, setApplicationPageSize] = useState(20);
  const [applicationTotal, setApplicationTotal] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const loadApplications = async () => {
      try {
        const offset = (applicationPage - 1) * applicationPageSize;
        const params = new URLSearchParams({
          limit: applicationPageSize.toString(),
          offset: offset.toString(),
        });
        if (submittedApplicationSearch) {
          params.set("search", submittedApplicationSearch);
        }
        const response = await apiFetch<ApplicationList>(
          `/applications?${params.toString()}`
        );
        if (!cancelled) {
          setApplications(response.items);
          setApplicationTotal(response.total);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load applications"
          );
        }
      }
    };
    loadApplications();
    return () => {
      cancelled = true;
    };
  }, [applicationPage, applicationPageSize, submittedApplicationSearch]);

  const totalPages = Math.max(1, Math.ceil(applicationTotal / applicationPageSize));

  const handleApplicationSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setApplicationPage(1);
    setSubmittedApplicationSearch(applicationSearch.trim());
  };

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

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Applications</h2>
              <p className="text-sm text-zinc-600">
                Browse applications and copy IDs for new RFIs.
              </p>
            </div>
            <form className="flex flex-wrap items-center gap-2" onSubmit={handleApplicationSearch}>
              <input
                className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                placeholder="Search by application ID"
                value={applicationSearch}
                onChange={(event) => setApplicationSearch(event.target.value)}
              />
              <button
                className="rounded-full border border-zinc-200 px-4 py-2 text-xs font-semibold text-zinc-600 hover:border-zinc-300"
                type="submit"
              >
                Search
              </button>
            </form>
          </div>
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-zinc-600">
            <div>
              Showing{" "}
              {applications.length === 0
                ? 0
                : (applicationPage - 1) * applicationPageSize + 1}{" "}
              -{" "}
              {Math.min(applicationPage * applicationPageSize, applicationTotal)}{" "}
              of {applicationTotal}
            </div>
            <div className="flex items-center gap-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Per page
              </label>
              <select
                className="rounded-lg border border-zinc-200 bg-white px-2 py-1 text-sm"
                value={applicationPageSize}
                onChange={(event) => {
                  setApplicationPageSize(Number(event.target.value));
                  setApplicationPage(1);
                }}
              >
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
            </div>
          </div>
          <div className="mt-4 overflow-hidden rounded-lg border border-zinc-200">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-100 text-xs uppercase text-zinc-500">
                <tr>
                  <th className="px-4 py-2">Application ID</th>
                  <th className="px-4 py-2">Customer ID</th>
                  <th className="px-4 py-2">Loan Amount</th>
                  <th className="px-4 py-2">Tenure</th>
                  <th className="px-4 py-2">Issue Status</th>
                  <th className="px-4 py-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {applications.length === 0 ? (
                  <tr>
                    <td className="px-4 py-3 text-sm text-zinc-500" colSpan={6}>
                      No applications found.
                    </td>
                  </tr>
                ) : (
                  applications.map((application) => (
                    <tr
                      key={application.application_id}
                      className="border-t border-zinc-200"
                    >
                      <td className="px-4 py-3">{application.application_id}</td>
                      <td className="px-4 py-3">{application.customer_id}</td>
                      <td className="px-4 py-3">
                        {application.requested_loan_amount.toLocaleString()}
                      </td>
                      <td className="px-4 py-3">
                        {application.requested_tenure_amount}
                      </td>
                      <td className="px-4 py-3">
                        {application.issue_status ?? "None"}
                      </td>
                      <td className="px-4 py-3">
                        {new Date(application.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="mt-4 flex items-center justify-between gap-3">
            <button
              className="rounded-full border border-zinc-200 px-4 py-2 text-xs font-semibold text-zinc-600 hover:border-zinc-300 disabled:opacity-60"
              type="button"
              onClick={() => setApplicationPage((prev) => Math.max(1, prev - 1))}
              disabled={applicationPage <= 1}
            >
              Previous
            </button>
            <span className="text-xs text-zinc-500">
              Page {applicationPage} of {totalPages}
            </span>
            <button
              className="rounded-full border border-zinc-200 px-4 py-2 text-xs font-semibold text-zinc-600 hover:border-zinc-300 disabled:opacity-60"
              type="button"
              onClick={() =>
                setApplicationPage((prev) => Math.min(totalPages, prev + 1))
              }
              disabled={applicationPage >= totalPages}
            >
              Next
            </button>
          </div>
          {error && (
            <p className="mt-3 text-sm text-red-600">Error: {error}</p>
          )}
        </section>

      </main>
    </div>
  );
}
