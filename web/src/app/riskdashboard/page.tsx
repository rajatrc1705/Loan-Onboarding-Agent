"use client";

import { apiBaseUrl, apiFetch } from "@/lib/api";
import { RfiCaseSummary } from "@/lib/types";
import { FormEvent, useEffect, useState } from "react";

export default function RiskDashboardPage() {
  const [customerEmail, setCustomerEmail] = useState("");
  const [applicationId, setApplicationId] = useState("");
  const [questions, setQuestions] = useState<string[]>([""]);
  const [cases, setCases] = useState<RfiCaseSummary[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastInvite, setLastInvite] = useState<RfiCaseSummary | null>(null);

  const loadCases = async () => {
    try {
      const response = await apiFetch<RfiCaseSummary[]>("/rfi");
      setCases(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load cases");
    }
  };

  useEffect(() => {
    loadCases();
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
      await loadCases();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create RFI");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 text-zinc-900">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <header className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Internal
          </p>
          <h1 className="text-2xl font-semibold">Risk Dashboard</h1>
          <p className="text-sm text-zinc-600">
            Create RFI cases, add questions, and send invites.
          </p>
        </header>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">New RFI</h2>
          <p className="mt-2 text-sm text-zinc-600">
            API base URL:{" "}
            <span className="font-mono text-xs text-zinc-800">
              {apiBaseUrl()}
            </span>
          </p>
          <form className="mt-4 grid gap-4" onSubmit={handleSubmit}>
            <div className="grid gap-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Customer Email
              </label>
              <input
                className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                placeholder="customer@company.com"
                value={customerEmail}
                onChange={(event) => setCustomerEmail(event.target.value)}
                required
              />
            </div>
            <div className="grid gap-2">
              <label className="text-xs font-semibold uppercase tracking-wide text-zinc-500">
                Application ID (optional)
              </label>
              <input
                className="rounded-lg border border-zinc-200 px-3 py-2 text-sm"
                placeholder="APP-1234"
                value={applicationId}
                onChange={(event) => setApplicationId(event.target.value)}
              />
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
          <h2 className="text-lg font-semibold">Live Cases</h2>
          <div className="mt-4 overflow-hidden rounded-lg border border-zinc-200">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-100 text-xs uppercase text-zinc-500">
                <tr>
                  <th className="px-4 py-2">Customer</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">Updated</th>
                  <th className="px-4 py-2">Links</th>
                </tr>
              </thead>
              <tbody>
                {cases.length === 0 ? (
                  <tr>
                    <td className="px-4 py-3 text-sm text-zinc-500" colSpan={4}>
                      No cases yet.
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
                        <div className="flex flex-col gap-1 text-xs">
                          <a className="underline" href={`/rfi/${item.id}`}>
                            View detail
                          </a>
                          {item.magic_token && (
                            <a
                              className="underline"
                              href={`/c/${item.magic_token}`}
                            >
                              Customer link
                            </a>
                          )}
                        </div>
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
