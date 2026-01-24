"use client";

import { apiFetch } from "@/lib/api";
import { RfiDetail } from "@/lib/types";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { Room } from "livekit-client";

export default function CallPage() {
  const params = useParams<{ id: string }>();
  const id = params?.id;
  const [detail, setDetail] = useState<RfiDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const room = useMemo(() => new Room(), []);

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

  return (
    <div className="min-h-screen bg-zinc-950 px-6 py-10 text-white">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
        <header className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-400">
            Live Call
          </p>
          <h1 className="text-2xl font-semibold">Clarification Call</h1>
          {detail?.room_name && (
            <p className="text-xs text-zinc-400">
              Room: <span className="font-mono">{detail.room_name}</span>
            </p>
          )}
        </header>

        {error && <p className="text-sm text-red-300">{error}</p>}

        <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
          <section className="rounded-2xl border border-zinc-800 bg-black p-4">
            <p className="text-xs font-semibold uppercase text-zinc-400">
              Agent Video
            </p>
            <video
              ref={videoRef}
              className="mt-3 h-[360px] w-full rounded-xl bg-zinc-900"
              autoPlay
              playsInline
              muted
            />
          </section>

          <section className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-4">
            <p className="text-xs font-semibold uppercase text-zinc-400">
              Controls
            </p>
            <div className="mt-4 flex flex-col gap-3">
              <button
                className="rounded-full bg-white px-4 py-2 text-sm font-semibold text-black disabled:opacity-60"
                type="button"
                onClick={handleConnect}
                disabled={!detail || isConnecting || isConnected}
              >
                {isConnected ? "Connected" : isConnecting ? "Connecting..." : "Join call"}
              </button>
              <button
                className="rounded-full border border-zinc-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                type="button"
                onClick={handleEndCall}
                disabled={!isConnected || isEnding}
              >
                {isEnding ? "Ending..." : "End call"}
              </button>
              <p className="text-xs text-zinc-400">
                Microphone is enabled after joining the room.
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
