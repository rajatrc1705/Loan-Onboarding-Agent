"use client";

import { apiFetch } from "@/lib/api";
import { CustomerRfiDetail } from "@/lib/types";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Room } from "livekit-client";

export default function CustomerMagicLinkPage() {
  const params = useParams<{ token: string }>();
  const token = params?.token;
  const [detail, setDetail] = useState<CustomerRfiDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const room = useMemo(() => new Room(), []);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    const loadDetail = async () => {
      try {
        const response = await apiFetch<CustomerRfiDetail>(`/c/${token}`);
        if (!cancelled) {
          setDetail(response);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load RFI");
        }
      }
    };
    loadDetail();
    const interval = setInterval(() => {
      if (!detail || detail.status === "DELIVERED") return;
      loadDetail();
    }, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [token, detail]);

  useEffect(() => {
    const handleTrackSubscribed = (track: any) => {
      if (track?.attach && videoRef.current) {
        track.attach(videoRef.current);
      }
    };

    room.on("trackSubscribed", handleTrackSubscribed);

    return () => {
      room.off("trackSubscribed", handleTrackSubscribed);
      room.disconnect();
    };
  }, [room]);

  const handleJoin = async () => {
    if (!detail) return;
    setError(null);
    setIsStarting(true);
    try {
      await apiFetch(`/rfi/${detail.id}/start-call`, { method: "POST" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start call");
    } finally {
      setIsStarting(false);
    }
  };

  const handleConnect = async () => {
    if (!detail?.room_name) {
      setError("Room is not ready yet.");
      return;
    }
    setError(null);
    setIsConnecting(true);
    try {
      const identity = `customer-${detail.id}`;
      const response = await apiFetch<{
        livekit_url: string;
        token: string;
      }>("/livekit/token", {
        method: "POST",
        body: JSON.stringify({
          room_name: detail.room_name,
          identity,
          name: "Customer",
          can_publish: true,
          can_subscribe: true,
        }),
      });
      await room.connect(response.livekit_url, response.token);
      await room.localParticipant.setMicrophoneEnabled(true);
      setIsConnected(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to join room");
    } finally {
      setIsConnecting(false);
    }
  };

  const handleEndCall = async () => {
    setIsEnding(true);
    try {
      await room.disconnect();
      setIsConnected(false);
    } finally {
      setIsEnding(false);
    }
  };

  const handleSubmit = async () => {
    if (!token) return;
    setError(null);
    setIsSubmitting(true);
    try {
      await apiFetch(`/c/${token}/submit`, { method: "POST" });
      const response = await apiFetch<CustomerRfiDetail>(`/c/${token}`);
      setDetail(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit answers");
    } finally {
      setIsSubmitting(false);
    }
  };

  const answersByQuestionId = useMemo(() => {
    const map = new Map<string, string>();
    detail?.answers?.forEach((answer) => {
      map.set(answer.question_id, answer.answer_text);
    });
    return map;
  }, [detail]);

  return (
    <div className="min-h-screen bg-zinc-50 px-6 py-12 text-zinc-900">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <header className="rounded-3xl border border-zinc-200 bg-gradient-to-br from-white via-white to-zinc-100 p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Customer
          </p>
          <h1 className="text-2xl font-semibold">We need a few clarifications</h1>
          <p className="text-sm text-zinc-600">
            Magic link token:{" "}
            <span className="font-mono text-xs text-zinc-800">{token}</span>
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">Step 1</p>
              <p className="mt-2 text-sm text-zinc-700">
                Review the questions and prepare your responses.
              </p>
            </div>
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">Step 2</p>
              <p className="mt-2 text-sm text-zinc-700">
                Join the call to answer each question.
              </p>
            </div>
            <div className="rounded-2xl border border-zinc-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-semibold uppercase text-zinc-500">Step 3</p>
              <p className="mt-2 text-sm text-zinc-700">
                Review your answers and submit when ready.
              </p>
            </div>
          </div>
        </header>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold">Questions</h2>
          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
          {detail ? (
            <div className="mt-4 grid gap-3">
              {detail.questions.length === 0 ? (
                <div className="rounded-lg border border-dashed border-zinc-200 p-4 text-sm text-zinc-600">
                  No questions yet.
                </div>
              ) : (
                detail.questions.map((question) => (
                  <div
                    key={question.id}
                    className="rounded-lg border border-zinc-200 p-4 text-sm text-zinc-700"
                  >
                    <p className="text-xs font-semibold uppercase text-zinc-500">
                      Question {question.order_index}
                    </p>
                    <p className="mt-1">{question.question_text}</p>
                  </div>
                ))
              )}
            </div>
          ) : (
            <div className="mt-4 h-24 rounded-lg border border-dashed border-zinc-200" />
          )}
        </section>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Join Call</h2>
            </div>
            {detail?.room_name && (
              <p className="text-xs text-zinc-500">
                Room: <span className="font-mono">{detail.room_name}</span>
              </p>
            )}
          </div>
          <div className="mt-4 grid gap-4 lg:grid-cols-[1.2fr_1fr]">
            <div className="rounded-2xl border border-dashed border-zinc-200 p-4">
              <p className="text-xs font-semibold uppercase text-zinc-500">Agent video</p>
              <video
                ref={videoRef}
                className="mt-2 h-56 w-full rounded-xl bg-black"
                autoPlay
                playsInline
                muted
              />
            </div>
            <div className="rounded-2xl border border-zinc-200 bg-zinc-50 p-4">
              <p className="text-xs font-semibold uppercase text-zinc-500">Call controls</p>
              <div className="mt-3 flex flex-col gap-3">
                <button
                  className="inline-flex items-center justify-center rounded-full bg-zinc-900 px-5 py-2 text-sm font-semibold text-white disabled:opacity-60"
                  type="button"
                  onClick={handleJoin}
                  disabled={!detail || isStarting}
                >
                  {isStarting ? "Starting..." : "Start agent"}
                </button>
                <button
                  className="inline-flex items-center justify-center rounded-full border border-zinc-200 px-5 py-2 text-sm font-semibold text-zinc-700 disabled:opacity-60"
                  type="button"
                  onClick={handleConnect}
                  disabled={!detail || isConnecting || isConnected}
                >
                  {isConnected ? "Connected" : isConnecting ? "Connecting..." : "Join call"}
                </button>
                <button
                  className="inline-flex items-center justify-center rounded-full border border-zinc-200 px-5 py-2 text-sm font-semibold text-zinc-700 disabled:opacity-60"
                  type="button"
                  onClick={handleEndCall}
                  disabled={!isConnected || isEnding}
                >
                  {isEnding ? "Ending..." : "End call"}
                </button>
                <p className="text-xs text-zinc-500">
                  Keep this tab open until the call completes.
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">Review your answers</h2>
              <p className="mt-2 text-sm text-zinc-600">
                After the call, review the summarized answers and submit when ready.
              </p>
            </div>
            {detail?.status === "DELIVERED" && (
              <span className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
                Submitted
              </span>
            )}
          </div>
          {detail?.answers?.length ? (
            <div className="mt-4 space-y-3">
              {detail.questions.map((question) => {
                const answer = answersByQuestionId.get(question.id);
                return (
                  <div
                    key={question.id}
                    className="rounded-lg border border-zinc-200 p-4 text-sm text-zinc-700"
                  >
                    <p className="text-xs font-semibold uppercase text-zinc-500">
                      Question {question.order_index}
                    </p>
                    <p className="mt-1">{question.question_text}</p>
                    <p className="mt-2 text-sm text-zinc-900">
                      <span className="font-semibold">Answer:</span>{" "}
                      {answer || "No answer captured."}
                    </p>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="mt-4 rounded-lg border border-dashed border-zinc-200 p-4 text-sm text-zinc-600">
              We will show your answers once they are captured.
            </div>
          )}
          <div className="mt-4 flex items-center gap-3">
            <button
              className="inline-flex items-center justify-center rounded-full bg-zinc-900 px-5 py-2 text-sm font-semibold text-white disabled:opacity-60"
              type="button"
              onClick={handleSubmit}
              disabled={!detail?.summary || isSubmitting || detail?.status === "DELIVERED"}
            >
              {detail?.status === "DELIVERED"
                ? "Submitted"
                : isSubmitting
                  ? "Submitting..."
                  : "Submit answers"}
            </button>
            {detail?.status === "DELIVERED" && (
              <p className="text-sm text-emerald-600">Thank you! Your answers were submitted.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
