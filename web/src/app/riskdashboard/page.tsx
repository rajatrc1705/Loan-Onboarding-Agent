"use client";

import { apiBaseUrl, apiFetch } from "@/lib/api";
import { Application, ApplicationList, RfiCaseSummary } from "@/lib/types";
import { FormEvent, useEffect, useMemo, useState } from "react";

export default function RiskDashboardPage() {
  const [customerEmail, setCustomerEmail] = useState("");
  const [customerEmailMode, setCustomerEmailMode] = useState<"existing" | "custom">(
    "custom"
  );
  const [customerEmails, setCustomerEmails] = useState<string[]>([]);
  const [applicationId, setApplicationId] = useState("");
  const [questions, setQuestions] = useState<string[]>([""]);
  const [cases, setCases] = useState<RfiCaseSummary[]>([]);
  const [applicationOptions, setApplicationOptions] = useState<Application[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastInvite, setLastInvite] = useState<RfiCaseSummary | null>(null);

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

  const loadCases = async () => {
    try {
      const response = await apiFetch<RfiCaseSummary[]>("/rfi");
      setCases(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cases");
    }
  };

  const loadCustomerEmails = async () => {
    try {
      const response = await apiFetch<string[]>("/rfi/customer-emails");
      setCustomerEmails(response);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load customer emails"
      );
    }
  };

  const loadApplicationOptions = async () => {
    try {
      const response = await apiFetch<ApplicationList>(
        "/applications?limit=1000&offset=0"
      );
      setApplicationOptions(response.items);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load application IDs"
      );
    }
  };

  useEffect(() => {
    loadCases();
    loadApplicationOptions();
    loadCustomerEmails();
  }, []);

  const updateQuestion = (index: number, value: string) => {
    setQuestions((prev) => prev.map((item, idx) => (idx === index ? value : item)));
  };

  const addQuestion = () => setQuestions((prev) => [...prev, ""]);

  const removeQuestion = (index: number) => {
    setQuestions((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    setLastInvite(null);
    try {
      const created = await apiFetch<RfiCaseSummary>("/rfi", {
        method: "POST",
        body: JSON.stringify({
          customer_email: customerEmail,
          application_id: applicationId || null,
        }),
      });

      const filteredQuestions = questions
        .map((text) => text.trim())
        .filter(Boolean)
        .map((questionText, index) => ({
          order_index: index + 1,
          question_text: questionText,
        }));

      if (filteredQuestions.length > 0) {
        await apiFetch(`/rfi/${created.id}/questions`, {
          method: "PUT",
          body: JSON.stringify({ questions: filteredQuestions }),
        });
      }

      const invited = await apiFetch<RfiCaseSummary>(
        `/rfi/${created.id}/send-invite`,
        { method: "POST" }
      );
      setLastInvite(invited);
      setCustomerEmail("");
      setApplicationId("");
      setQuestions([""]);
      setCustomerEmailMode("custom");
      await loadCases();
      await loadApplicationOptions();
      await loadCustomerEmails();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create RFI");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (caseId: string, email: string) => {
    const confirmed = window.confirm(
      `Delete the case for ${email}? This will remove the questions and answers.`
    );
    if (!confirmed) return;
    setError(null);
    setDeletingId(caseId);
    try {
      await apiFetch(`/rfi/${caseId}`, { method: "DELETE" });
      await loadCases();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete case");
    } finally {
      setDeletingId(null);
    }
  };


  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 text-zinc-900">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <header className="rounded-3xl border border-zinc-200 bg-gradient-to-br from-white via-white to-zinc-100 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Internal
          </p>
          <h1 className="text-2xl font-semibold">Risk Dashboard</h1>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
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
              <p className="text-xs font-semibold uppercase text-zinc-500">Delivered</p>
              <p className="mt-2 text-2xl font-semibold text-emerald-700">{stats.delivered}</p>
            </div>
          </div>
        </header>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">New RFI</h2>
          <form className="mt-4 grid gap-4" onSubmit={handleSubmit}>
            <div className="grid gap-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Customer Email
              </label>
              <div className="grid gap-2 sm:grid-cols-[160px_1fr]">
                <select
                  className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                  value={customerEmailMode}
                  onChange={(event) => {
                    const mode = event.target.value as "existing" | "custom";
                    setCustomerEmailMode(mode);
                    if (mode === "existing") {
                      setCustomerEmail("");
                    }
                  }}
                >
                  <option value="custom">Custom email</option>
                  <option value="existing">Existing customer</option>
                </select>
                {customerEmailMode === "existing" ? (
                  <select
                    className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                    value={customerEmail}
                    onChange={(event) => setCustomerEmail(event.target.value)}
                    required
                  >
                    <option value="">Select a customer email</option>
                    {customerEmails.map((email) => (
                      <option key={email} value={email}>
                        {email}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                    placeholder="customer@company.com"
                    value={customerEmail}
                    onChange={(event) => setCustomerEmail(event.target.value)}
                    required
                  />
                )}
              </div>
            </div>
            <div className="grid gap-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Application ID (optional)
              </label>
              <select
                className="rounded-lg border border-zinc-200 bg-white px-3 py-2 text-sm"
                value={applicationId}
                onChange={(event) => setApplicationId(event.target.value)}
              >
                <option value="">Select an application ID</option>
                {applicationOptions.map((application) => (
                  <option
                    key={application.application_id}
                    value={application.application_id}
                  >
                    {application.application_id}
                  </option>
                ))}
              </select>
            </div>
            <div className="grid gap-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Questions
              </label>
              <div className="grid gap-2">
                {questions.map((question, index) => (
                  <div key={`question-${index}`} className="flex gap-2">
                    <input
                      className="flex-1 rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                      placeholder={`Question ${index + 1}`}
                      value={question}
                      onChange={(event) =>
                        updateQuestion(index, event.target.value)
                      }
                    />
                    {questions.length > 1 && (
                      <button
                        className="rounded-lg border border-zinc-200 px-3 text-xs font-semibold text-zinc-500"
                        type="button"
                        onClick={() => removeQuestion(index)}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                ))}
              </div>
              <button
                className="w-fit rounded-lg border border-zinc-200 px-3 py-1 text-xs font-semibold text-zinc-600"
                type="button"
                onClick={addQuestion}
              >
                Add question
              </button>
            </div>
            <button
              className="w-fit rounded-full bg-zinc-900 px-5 py-2 text-sm font-semibold text-white"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Sending..." : "Send invite"}
            </button>
            {error && (
              <p className="text-sm text-red-600">Error: {error}</p>
            )}
            {lastInvite?.magic_token && (
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                Invite sent. Magic link:{" "}
                <a
                  className="font-semibold underline"
                  href={`/c/${lastInvite.magic_token}`}
                >
                  /c/{lastInvite.magic_token}
                </a>
              </div>
            )}
          </form>
        </section>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-lg font-semibold">Live Cases</h2>
              <p className="text-sm text-zinc-600">
                Track current RFI status and jump to customer links.
              </p>
            </div>
            <button
              className="rounded-full border border-zinc-200 px-4 py-2 text-xs font-semibold text-zinc-600 hover:border-zinc-300"
              type="button"
              onClick={loadCases}
            >
              Refresh list
            </button>
          </div>
          <div className="mt-4 overflow-hidden rounded-lg border border-zinc-200">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-100 text-xs uppercase text-zinc-500">
                <tr>
                  <th className="px-4 py-2">Customer</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">Updated</th>
                  <th className="px-4 py-2">Summary</th>
                  <th className="px-4 py-2 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {cases.length === 0 ? (
                  <tr>
                    <td className="px-4 py-3 text-sm text-zinc-500" colSpan={5}>
                      No cases yet.
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
                        <a
                          className="inline-flex rounded-full bg-zinc-100 px-3 py-1 text-xs font-semibold text-zinc-700 hover:bg-zinc-200"
                          href={`/rfi/${item.id}`}
                        >
                          Summary
                        </a>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          className="rounded-full border border-red-200 px-3 py-1 text-xs font-semibold text-red-600 hover:border-red-300 disabled:opacity-60"
                          type="button"
                          onClick={() => handleDelete(item.id, item.customer_email)}
                          disabled={deletingId === item.id}
                        >
                          {deletingId === item.id ? "Deleting..." : "Delete"}
                        </button>
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
