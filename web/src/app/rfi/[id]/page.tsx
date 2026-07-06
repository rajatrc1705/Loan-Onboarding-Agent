"use client";

import { apiFetch } from "@/lib/api";
import { RfiDetail } from "@/lib/types";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

type ReviewPacket = {
  short_summary?: string;
  follow_up_needed?: Array<{
    question_id?: string;
    question_text?: string;
    answer_status?: string;
  }>;
};

const answerBadge = (status: string) => {
  const styles: Record<string, string> = {
    answered: "bg-emerald-100 text-emerald-700",
    unclear: "bg-amber-100 text-amber-700",
    not_answered: "bg-red-100 text-red-700",
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

  const answersByQuestionId = useMemo(() => {
    const map = new Map<string, RfiDetail["answers"][number]>();
    detail?.answers.forEach((answer) => {
      map.set(answer.question_id, answer);
    });
    return map;
  }, [detail]);

  const reviewPacket = detail?.summary?.structured_json as ReviewPacket | undefined;

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 text-zinc-900">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <header className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Internal
          </p>
          <h1 className="text-2xl font-semibold">RFI Detail</h1>
          <p className="text-sm text-zinc-600">
            Case ID: <span className="font-mono text-xs text-zinc-800">{id}</span>
          </p>
        </header>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Case Summary</h2>
              {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
            </div>
            {detail?.needs_review && (
              <span className="inline-flex rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                Needs review
              </span>
            )}
          </div>
          {detail ? (
            <div className="mt-4 grid gap-3 text-sm text-zinc-600 sm:grid-cols-2">
              <div>
                <span className="font-semibold text-zinc-800">Customer:</span>{" "}
                {detail.customer_email}
              </div>
              <div>
                <span className="font-semibold text-zinc-800">Status:</span>{" "}
                {detail.status.replace("_", " ")}
              </div>
              {detail.review_reason && (
                <div className="sm:col-span-2">
                  <span className="font-semibold text-zinc-800">Review reason:</span>{" "}
                  {detail.review_reason}
                </div>
              )}
              {detail.magic_token && (
                <div className="sm:col-span-2">
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
          <h2 className="text-lg font-semibold">Review Packet</h2>
          <p className="mt-2 whitespace-pre-wrap text-sm text-zinc-700">
            {detail?.summary?.summary_text ?? "No review packet yet."}
          </p>
          {reviewPacket?.follow_up_needed?.length ? (
            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              <p className="text-xs font-semibold uppercase">Follow-up needed</p>
              <div className="mt-2 grid gap-1">
                {reviewPacket.follow_up_needed.map((item, index) => (
                  <p key={`${item.question_id ?? index}`}>
                    {item.question_text ?? item.question_id}{" "}
                    {item.answer_status ? `(${item.answer_status})` : ""}
                  </p>
                ))}
              </div>
            </div>
          ) : null}
        </section>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Question Answers</h2>
          {detail ? (
            <div className="mt-4 grid gap-3">
              {detail.questions.map((question) => {
                const answer = answersByQuestionId.get(question.id);
                return (
                  <div key={question.id} className="rounded-lg border border-zinc-200 p-4">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-xs font-semibold uppercase text-zinc-500">
                          Question {question.order_index}
                        </p>
                        <p className="mt-1 text-sm text-zinc-900">
                          {question.question_text}
                        </p>
                      </div>
                      {answer ? answerBadge(answer.answer_status) : answerBadge("not_answered")}
                    </div>
                    <p className="mt-3 text-sm text-zinc-700">
                      {answer?.answer_text || "No answer captured."}
                    </p>
                    {answer?.evidence_quote && (
                      <p className="mt-2 text-xs text-zinc-500">
                        Evidence: {answer.evidence_quote}
                      </p>
                    )}
                    {answer?.evaluator_notes && (
                      <p className="mt-2 text-xs text-zinc-500">
                        Evaluator: {answer.evaluator_notes}
                      </p>
                    )}
                    {answer?.follow_up_asked && (
                      <p className="mt-2 text-xs font-semibold text-amber-700">
                        Follow-up was asked.
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="mt-4 h-32 rounded-lg border border-dashed border-zinc-200" />
          )}
        </section>

        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold">Customer Questions</h2>
            <div className="mt-4 grid gap-3 text-sm text-zinc-700">
              {detail?.customer_questions?.length ? (
                detail.customer_questions.map((question) => (
                  <div key={question.id} className="rounded-lg border border-zinc-200 p-3">
                    <p>{question.question_text}</p>
                    {question.agent_response && (
                      <p className="mt-2 text-zinc-500">
                        Agent: {question.agent_response}
                      </p>
                    )}
                    <p className="mt-2 text-xs font-semibold uppercase text-zinc-500">
                      {question.needs_human_followup
                        ? "Needs human follow-up"
                        : "Answered on call"}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-zinc-500">No customer questions captured.</p>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
            <h2 className="text-lg font-semibold">Transcript</h2>
            <div className="mt-4 max-h-96 overflow-auto rounded-lg border border-zinc-200">
              {detail?.transcript?.length ? (
                detail.transcript.map((turn) => (
                  <div key={turn.id} className="border-b border-zinc-100 p-3 text-sm last:border-b-0">
                    <p className="text-xs font-semibold uppercase text-zinc-500">
                      {turn.speaker}
                    </p>
                    <p className="mt-1 text-zinc-700">{turn.text}</p>
                  </div>
                ))
              ) : (
                <p className="p-3 text-sm text-zinc-500">No transcript captured.</p>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
