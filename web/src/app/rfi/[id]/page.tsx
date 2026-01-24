"use client";

import { apiFetch } from "@/lib/api";
import { RfiDetail } from "@/lib/types";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function RfiDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const [detail, setDetail] = useState<RfiDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const loadDetail = async () => {
      try {
        const response = await apiFetch<RfiDetail>(`/rfi/${id}`);
        setDetail(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load case");
      }
    };
    loadDetail();
  }, [id]);

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 text-zinc-900">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6">
        <header className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Internal
          </p>
          <h1 className="text-2xl font-semibold">RFI Detail</h1>
          <p className="text-sm text-zinc-600">
            Case ID:{" "}
            <span className="font-mono text-xs text-zinc-800">{id}</span>
          </p>
        </header>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Case Summary</h2>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          {detail ? (
            <div className="mt-4 grid gap-3 text-sm text-zinc-600">
              <div>
                <span className="font-semibold text-zinc-800">Customer:</span>{" "}
                {detail.customer_email}
              </div>
              <div>
                <span className="font-semibold text-zinc-800">Status:</span>{" "}
                {detail.status}
              </div>
              {detail.magic_token && (
                <div>
                  <span className="font-semibold text-zinc-800">Magic link:</span>{" "}
                  <a className="underline" href={`/c/${detail.magic_token}`}>
                    /c/{detail.magic_token}
                  </a>
                </div>
              )}
            </div>
          ) : (
            <div className="mt-4 h-24 rounded-lg border border-dashed border-zinc-200" />
          )}
        </section>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Answers & Summary</h2>
          {detail ? (
            <div className="mt-4 grid gap-4 text-sm text-zinc-700">
              <div className="rounded-lg border border-zinc-200 p-4">
                <p className="text-xs font-semibold uppercase text-zinc-500">
                  Summary
                </p>
                <p className="mt-2 whitespace-pre-wrap">
                  {detail.summary?.summary_text ?? "No summary yet."}
                </p>
              </div>
              <div className="rounded-lg border border-zinc-200 p-4">
                <p className="text-xs font-semibold uppercase text-zinc-500">
                  Answers
                </p>
                <div className="mt-2 grid gap-2">
                  {detail.answers.length === 0 ? (
                    <p className="text-sm text-zinc-500">No answers yet.</p>
                  ) : (
                    detail.answers.map((answer) => (
                      <div
                        key={answer.id}
                        className="rounded-lg border border-dashed border-zinc-200 p-3"
                      >
                        <p className="text-xs text-zinc-500">
                          Question ID: {answer.question_id}
                        </p>
                        <p className="mt-1">{answer.answer_text}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="mt-4 h-32 rounded-lg border border-dashed border-zinc-200" />
          )}
        </section>
      </div>
    </div>
  );
}
