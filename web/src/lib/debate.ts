// The advisors' debate room as the screen sees it: a session's events (streamed live from
// POST /v1/debate/sessions, or a saved session from GET /v1/debate/sessions/{id}) folded into one
// state. Pure functions only, so they run in node:test (debate.test.ts) and in the browser.

export const STAGES = ["brief", "openings", "faultlines", "debate", "vote", "verdict"] as const;
export type Stage = (typeof STAGES)[number];

export type SeatInfo = {
  id: string;
  role: "advisor" | "chair";
  name_en: string;
  name_ar: string;
  initials: string;
  lens_en: string;
  lens_ar: string;
  portrait: string | null;
  /** The name on the tag and in the debate ("Alwaleed"); older sessions lack it. */
  short_en?: string;
  short_ar?: string;
  /** Ticker keys of companies the person is tied to: the seat sits out sessions about them. */
  recuse?: string[];
};

export type Flags = { unverified: string[]; cited: number; removed: number };
export type Option = { id: string; label: string; detail: string };
export type Brief = { question: string; options: Option[]; focus: string[]; weighing: Record<string, string>; note: string };
export type Absent = { absent: true; error: string };
export type Opening = { lean: string; headline: string; text: string };
export type Reply = Opening & { responds_to: string | null; changed: boolean };
export type FaultLines = { lines: { title: string; between: string[]; text: string }[]; summary: string };
export type Vote = { scores: Record<string, number>; top: string; reason: string };
export type Credited = { seat: string | null; point: string };
export type Verdict = {
  headline: string;
  summary: string;
  why: Credited[];
  watch_out: Credited | null;
  disagreements: string[];
  gaps: string[];
};
export type Result = {
  average: Record<string, number | null>;
  best: string[];
  agreement: number;
  voters: number;
  scores: Record<string, Record<string, number>>;
  labels?: Record<string, string>;
  headline?: string | null;
};

export type Turn = {
  stage: Stage;
  round: number | null;
  seat: string;
  data: Record<string, unknown>;
  flags: Flags | null;
  seconds?: number | null;
};

export type Source = { title_en: string; title_ar: string; ok: boolean };
export type TickerRef = { slug: string; symbol: string; name_en: string | null; name_ar: string | null };

export type SessionMeta = {
  id: number;
  ticker: TickerRef | null;
  ticker_key: string;
  question: string;
  locale: string;
  status: "running" | "done" | "failed" | string;
  created_at: string;
  seconds: number | null;
  result: Result | null;
  seats: SeatInfo[];
  models: Record<string, string>;
  rounds: number;
  sources: Record<string, Source> | null;
  error: string | null;
  turns?: Turn[];
};

export type DebateEvent =
  | { type: "session"; session: SessionMeta }
  | { type: "stage"; stage: Stage; round: number | null; rounds: number }
  | { type: "writing"; seats: string[] }
  | { type: "turn"; turn: Turn }
  | { type: "result"; result: Result }
  | { type: "error"; code: string }
  | { type: "done"; status: string; seconds: number | null; result: Result | null };

export type Room = {
  session: SessionMeta | null;
  status: "idle" | "running" | "done" | "failed";
  stage: Stage | null;
  round: number | null;
  writing: string[];
  turns: Turn[];
  result: Result | null;
  error: string | null;
  seconds: number | null;
};

export const EMPTY_ROOM: Room = {
  session: null,
  status: "idle",
  stage: null,
  round: null,
  writing: [],
  turns: [],
  result: null,
  error: null,
  seconds: null,
};

export function applyEvent(room: Room, e: DebateEvent): Room {
  switch (e.type) {
    case "session":
      return { ...EMPTY_ROOM, session: e.session, status: "running", stage: "brief" };
    case "stage":
      return { ...room, stage: e.stage, round: e.round };
    case "writing":
      return { ...room, writing: e.seats };
    case "turn":
      return { ...room, turns: [...room.turns, e.turn] };
    case "result":
      return { ...room, result: e.result };
    case "error":
      return { ...room, error: e.code };
    case "done":
      return {
        ...room,
        status: e.status === "done" ? "done" : "failed",
        writing: [],
        seconds: e.seconds,
        result: e.result ?? room.result,
        session: room.session ? { ...room.session, status: e.status, seconds: e.seconds, result: e.result ?? room.session.result } : null,
      };
  }
}

/** A saved session (finished, failed or still running on the server) as a room. */
export function roomFromSession(s: SessionMeta): Room {
  const turns = s.turns ?? [];
  const last = turns[turns.length - 1];
  const status = s.status === "done" ? "done" : s.status === "failed" ? "failed" : "running";
  let stage: Stage | null = last ? last.stage : "brief";
  let round = last?.round ?? null;
  if (status === "running" && last) {
    // The next step, if this one is complete.
    const next = nextStep(s, turns);
    stage = next.stage;
    round = next.round;
  }
  return {
    session: s,
    status,
    stage,
    round,
    writing: status === "running" ? writingNext(s, turns) : [],
    turns,
    result: s.result,
    error: s.error,
    seconds: s.seconds,
  };
}

const advisorIds = (s: SessionMeta) => s.seats.filter((x) => x.role === "advisor").map((x) => x.id);

/** Every step of a session in order: [stage, round, seats]. */
export function steps(s: SessionMeta): { stage: Stage; round: number | null; seats: string[] }[] {
  const advisors = advisorIds(s);
  const debates = Math.max(s.rounds - 2, 0);
  return [
    { stage: "brief", round: null, seats: ["chair"] },
    { stage: "openings", round: 1, seats: advisors },
    { stage: "faultlines", round: null, seats: ["chair"] },
    ...Array.from({ length: debates }, (_, i) => ({ stage: "debate" as Stage, round: 2 + i, seats: advisors })),
    { stage: "vote", round: s.rounds, seats: advisors },
    { stage: "verdict", round: null, seats: ["chair"] },
  ];
}

function nextStep(s: SessionMeta, turns: Turn[]) {
  for (const step of steps(s)) {
    const done = turns.filter((t) => t.stage === step.stage && t.round === step.round).length;
    if (done < step.seats.length) return step;
  }
  return { stage: "verdict" as Stage, round: null, seats: [] };
}

function writingNext(s: SessionMeta, turns: Turn[]): string[] {
  const step = nextStep(s, turns);
  const done = new Set(turns.filter((t) => t.stage === step.stage && t.round === step.round).map((t) => t.seat));
  return step.seats.filter((x) => !done.has(x));
}

/** Share of the session's steps finished (each seat's answer is one), 0 to 1. */
export function progress(room: Room): number {
  if (!room.session) return 0;
  const total = steps(room.session).reduce((n, st) => n + st.seats.length, 0);
  return total ? Math.min(room.turns.length / total, 1) : 0;
}

/** Share of the current step's seats that have answered, 0 to 1. */
export function stepProgress(room: Room): number {
  if (!room.session || !room.stage) return 0;
  const step = steps(room.session).find((st) => st.stage === room.stage && (st.round === room.round || st.seats.includes("chair")));
  if (!step) return 0;
  const done = room.turns.filter((t) => t.stage === step.stage && t.round === step.round).length;
  return Math.min(done / step.seats.length, 1);
}

export function turnsOf(room: Room, stage: Stage, round?: number | null): Turn[] {
  return room.turns.filter((t) => t.stage === stage && (round === undefined || t.round === round));
}

export const isAbsent = (d: Record<string, unknown>): boolean => d.absent === true;

export function briefOf(room: Room): Brief | null {
  const t = room.turns.find((x) => x.stage === "brief");
  return t && !isAbsent(t.data) ? (t.data as unknown as Brief) : null;
}

export function verdictOf(room: Room): Verdict | null {
  const t = room.turns.find((x) => x.stage === "verdict");
  return t && !isAbsent(t.data) ? (t.data as unknown as Verdict) : null;
}

/** The option a seat leans to now: its last reply's lean, else its opening's. */
export function leanOf(room: Room, seat: string): string | null {
  const said = room.turns.filter((t) => t.seat === seat && (t.stage === "openings" || t.stage === "debate") && !isAbsent(t.data));
  const last = said[said.length - 1];
  return last ? (last.data.lean as string) : null;
}

export function voteOf(room: Room, seat: string): Vote | null {
  const t = room.turns.find((x) => x.stage === "vote" && x.seat === seat);
  return t && !isAbsent(t.data) ? (t.data as unknown as Vote) : null;
}

/** Which stages the tabs can open: those with at least one answer, plus the live one. */
export function reached(room: Room): Set<Stage> {
  const out = new Set<Stage>(room.turns.map((t) => t.stage));
  if (room.stage && room.status === "running") out.add(room.stage);
  return out;
}

/** An average score as computed, two decimals at most ("6.75", "6.5", "8.0"), or null. With four
 *  advisors every average is exact at two decimals, so the screen and the Chair quote the same figure. */
export function fmtScore(v: number | null | undefined): string | null {
  if (v == null || !Number.isFinite(v)) return null;
  return (Math.round(v * 100) / 100).toFixed(2).replace(/(\.\d)0$/, "$1");
}

/** The first sentence of a seat's text, for the key points. */
export function firstSentence(text: string): string {
  const m = text.match(/^[\s\S]+?[.!?؟](?=\s|$)/);
  return (m ? m[0] : text).trim();
}

/** "1:05" from seconds. */
export function fmtElapsed(seconds: number | null | undefined): string | null {
  if (seconds == null || !Number.isFinite(seconds)) return null;
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/**
 * Server-sent events from a fetch body: complete `data: {...}` blocks, and the unfinished rest
 * to prepend to the next chunk. Comment lines (": keepalive") are skipped.
 */
export function parseSse(buffer: string): { events: DebateEvent[]; rest: string } {
  const blocks = buffer.replace(/\r/g, "").split("\n\n");
  const rest = blocks.pop() ?? "";
  const events: DebateEvent[] = [];
  for (const block of blocks) {
    const data = block
      .split("\n")
      .filter((l) => l.startsWith("data:"))
      .map((l) => l.slice(5).trimStart())
      .join("\n");
    if (!data || data === "[DONE]") continue;
    try {
      events.push(JSON.parse(data) as DebateEvent);
    } catch {
      // A malformed block is dropped; the saved session fills any gap when the stream ends.
    }
  }
  return { events, rest };
}

/** Pieces of a seat's text: plain runs, citation tags ([P1]) and figures the checks could not find in the data. */
export type Piece = { kind: "text" | "tag" | "unverified"; text: string };

export function splitText(text: string, unverified: string[] = []): Piece[] {
  const figures = [...new Set(unverified)].filter(Boolean).sort((a, b) => b.length - a.length);
  const escaped = figures.map((f) => f.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const pattern = new RegExp(
    `(\\[P\\d+\\]|\\[DB\\]${escaped.length ? `|(?<![\\d.,])(?:${escaped.join("|")})(?![\\d])` : ""})`,
    "g",
  );
  const out: Piece[] = [];
  for (const part of text.split(pattern)) {
    if (!part) continue;
    if (/^\[(P\d+|DB)\]$/.test(part)) out.push({ kind: "tag", text: part.slice(1, -1) });
    else if (figures.includes(part)) out.push({ kind: "unverified", text: part });
    else out.push({ kind: "text", text: part });
  }
  return out;
}
