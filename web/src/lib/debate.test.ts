// Run with: npm test   (Node's built-in runner; Node 24 strips the types)
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  EMPTY_ROOM,
  applyEvent,
  fmtElapsed,
  fmtScore,
  leanOf,
  parseSse,
  progress,
  reached,
  roomFromSession,
  splitText,
  stepProgress,
  steps,
  type DebateEvent,
  type SessionMeta,
} from "./debate.ts";

const seat = (id: string, role: "advisor" | "chair" = "advisor") => ({
  id,
  role,
  name_en: id,
  name_ar: id,
  initials: id.slice(0, 2).toUpperCase(),
  lens_en: "",
  lens_ar: "",
  portrait: null,
});

const SESSION: SessionMeta = {
  id: 42,
  ticker: { slug: "2222", symbol: "2222", name_en: "Saudi Aramco", name_ar: null },
  ticker_key: "2222_TADAWUL",
  question: "Is the dividend covered?",
  locale: "en",
  status: "running",
  created_at: "2026-10-18T10:00:00Z",
  seconds: null,
  result: null,
  seats: [seat("buffett"), seat("marks"), seat("chair", "chair")],
  models: { advisors: "a", chair: "c" },
  rounds: 3,
  sources: null,
  error: null,
};

const turn = (stage: string, round: number | null, s: string, data: Record<string, unknown>) =>
  ({ type: "turn", turn: { stage, round, seat: s, data, flags: null } }) as DebateEvent;

test("steps: brief, openings, fault lines, each debate round, vote, verdict", () => {
  assert.deepEqual(
    steps(SESSION).map((s) => `${s.stage}:${s.round ?? "-"}:${s.seats.length}`),
    ["brief:-:1", "openings:1:2", "faultlines:-:1", "debate:2:2", "vote:3:2", "verdict:-:1"],
  );
  assert.equal(steps({ ...SESSION, rounds: 4 }).filter((s) => s.stage === "debate").length, 2);
});

test("events fold into the room, and progress counts each seat's answer", () => {
  let room = applyEvent(EMPTY_ROOM, { type: "session", session: SESSION });
  assert.equal(room.status, "running");
  room = applyEvent(room, turn("brief", null, "chair", { question: "q", options: [], focus: [], weighing: {}, note: "" }));
  room = applyEvent(room, { type: "stage", stage: "openings", round: 1, rounds: 3 });
  room = applyEvent(room, { type: "writing", seats: ["buffett", "marks"] });
  room = applyEvent(room, turn("openings", 1, "marks", { lean: "B", headline: "h", text: "t" }));
  assert.equal(stepProgress(room), 0.5);
  assert.equal(progress(room), 2 / 9); // 1 + 2 + 1 + 2 + 2 + 1 answers in all
  assert.equal(leanOf(room, "marks"), "B");
  room = applyEvent(room, turn("debate", 2, "marks", { lean: "A", headline: "h", text: "t", responds_to: null, changed: true }));
  assert.equal(leanOf(room, "marks"), "A");
  assert.equal(leanOf(room, "buffett"), null);
  assert.deepEqual([...reached(room)].sort(), ["brief", "debate", "openings"]);
  room = applyEvent(room, { type: "done", status: "failed", seconds: 61.5, result: null });
  assert.equal(room.status, "failed");
  assert.deepEqual(room.writing, []);
  assert.equal(room.session?.status, "failed");
});

test("a saved session that is still running resumes at its next step", () => {
  const saved: SessionMeta = {
    ...SESSION,
    turns: [
      { stage: "brief", round: null, seat: "chair", data: {}, flags: null },
      { stage: "openings", round: 1, seat: "buffett", data: { lean: "A" }, flags: null },
    ],
  };
  const room = roomFromSession(saved);
  assert.equal(room.stage, "openings");
  assert.deepEqual(room.writing, ["marks"]);
  const done = roomFromSession({ ...saved, status: "done", turns: [...saved.turns!, { stage: "verdict", round: null, seat: "chair", data: {}, flags: null }] });
  assert.equal(done.stage, "verdict");
  assert.equal(done.status, "done");
  assert.deepEqual(done.writing, []);
});

test("server-sent events: whole blocks parsed, keep-alives skipped, the unfinished tail kept", () => {
  const chunk = 'data: {"type":"writing","seats":["chair"]}\n\n: keepalive\n\ndata: {"type":"stage","stage":"brief"';
  const { events, rest } = parseSse(chunk);
  assert.deepEqual(events, [{ type: "writing", seats: ["chair"] }]);
  assert.equal(rest, 'data: {"type":"stage","stage":"brief"');
  const next = parseSse(rest + ',"round":null,"rounds":3}\n\n');
  assert.equal(next.events[0].type, "stage");
  assert.equal(next.rest, "");
});

test("text pieces: citation tags and unverified figures are marked, other digits are not", () => {
  const pieces = splitText("ROE is 26.75% [P1] and P/E 99.9, not 199.9 [P2].", ["99.9"]);
  assert.deepEqual(
    pieces.filter((p) => p.kind !== "text"),
    [
      { kind: "tag", text: "P1" },
      { kind: "unverified", text: "99.9" },
      { kind: "tag", text: "P2" },
    ],
  );
  assert.equal(pieces.map((p) => (p.kind === "tag" ? `[${p.text}]` : p.text)).join(""), "ROE is 26.75% [P1] and P/E 99.9, not 199.9 [P2].");
});

test("scores and times", () => {
  assert.equal(fmtScore(6.25), "6.3");
  assert.equal(fmtScore(13 / 3), "4.3");
  assert.equal(fmtScore(7), "7.0");
  assert.equal(fmtScore(null), null);
  assert.equal(fmtElapsed(65.4), "1:05");
  assert.equal(fmtElapsed(null), null);
});
