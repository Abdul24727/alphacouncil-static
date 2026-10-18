"use client";

import { useQuery } from "@tanstack/react-query";
import { api, ApiError, unwrap } from "@/lib/api/client";
import { parseSse, type DebateEvent, type SessionMeta } from "@/lib/debate";

// Advisors' debate room (api/app/routers/debate.py). The session itself streams over fetch:
// the shared client times requests out after 30 s, and a session takes a few minutes.

export const DEBATE_KEY = ["debate"] as const;

export function useDebateStatus() {
  return useQuery({
    queryKey: [...DEBATE_KEY, "status"],
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/debate/status", { signal })),
    staleTime: 30_000,
  });
}

export function useDebateSessions(enabled: boolean) {
  return useQuery({
    queryKey: [...DEBATE_KEY, "sessions"],
    queryFn: async ({ signal }) => unwrap(await api.GET("/v1/debate/sessions", { signal })),
    enabled,
  });
}

/** One saved session, re-read every few seconds while it is still running on the server. */
export function useDebateSession(id: number | null) {
  return useQuery({
    queryKey: [...DEBATE_KEY, "session", id],
    queryFn: async ({ signal }) =>
      unwrap(await api.GET("/v1/debate/sessions/{session_id}", { params: { path: { session_id: id! } }, signal })) as unknown as SessionMeta,
    enabled: id != null,
    refetchInterval: (q) => (q.state.data?.status === "running" ? 3_000 : false),
  });
}

/** Convene the advisors and hand each event to `onEvent` as it arrives. Rejects with ApiError
 *  (detail = the API's code: pro_required, debate_limit, debate_running…) before the stream starts. */
export async function streamDebate(
  body: { ticker: string; question: string; locale: "en" | "ar" },
  onEvent: (e: DebateEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch("/api/v1/debate/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok || !res.body) {
    let detail = `HTTP ${res.status}`;
    try {
      const err = (await res.json()) as { detail?: unknown };
      if (typeof err.detail === "string") detail = err.detail;
    } catch {
      // Not JSON (a proxy error page): keep the status.
    }
    throw new ApiError(res.status, detail);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const { events, rest } = parseSse(buffer);
    buffer = rest;
    events.forEach(onEvent);
  }
  parseSse(buffer + "\n\n").events.forEach(onEvent);
}
