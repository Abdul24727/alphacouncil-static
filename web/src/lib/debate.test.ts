// Run with: npm test   (Node's built-in runner; Node 24 strips the types)
import assert from "node:assert/strict";
import { test } from "node:test";
import {
  EMPTY_ROOM,
  applyEvent,
  clip,
  lineMs,
  lineOf,
  fmtElapsed,
  firstSentence,
  fmtScore,
  leanOf,
  modeOf,
  parseSse,
  progress,
  reached,
  roomFromSession,
  splitText,
  stagesOf,
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

test("steps: brief, answers, fault lines, each round of challenges, final word, the answer", () => {
  assert.deepEqual(
    steps(SESSION).map((s) => `${s.stage}:${s.round ?? "-"}:${s.seats.length}`),
    ["brief:-:1", "openings:1:2", "faultlines:-:1", "debate:2:2", "final:3:2", "verdict:-:1"],
  );
  assert.equal(steps({ ...SESSION, rounds: 4 }).filter((s) => s.stage === "debate").length, 2);
  assert.deepEqual(stagesOf(SESSION), ["brief", "openings", "faultlines", "debate", "final", "verdict"]);
});

test("a session held in the scored format keeps its vote stage", () => {
  const scored: SessionMeta = {
    ...SESSION,
    status: "done",
    turns: [
      { stage: "brief", round: null, seat: "chair", data: { question: "q", options: [{ id: "A", label: "l", detail: "" }] }, flags: null },
      { stage: "vote", round: 3, seat: "buffett", data: { scores: { A: 7 }, top: "A", reason: "r" }, flags: null },
    ],
  };
  assert.deepEqual(stagesOf(scored), ["brief", "openings", "faultlines", "debate", "vote", "verdict"]);
  assert.equal(steps(scored).find((s) => s.round === 3)?.stage, "vote");
  // No mode was stored then: options meant a choice.
  assert.equal(modeOf(roomFromSession(scored)), "choice");
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
  assert.equal(modeOf(room), "open"); // the brief framed no options
  assert.equal(leanOf(room, "marks"), "B");
  room = applyEvent(room, turn("debate", 2, "marks", { lean: "A", headline: "h", text: "t", responds_to: null, changed: true }));
  assert.equal(leanOf(room, "marks"), "A");
  assert.equal(leanOf(room, "buffett"), null);
  // The final word is the latest lean there is.
  room = applyEvent(room, turn("final", 3, "marks", { lean: "B", lean_changed: true, text: "t", changed: "c", would_change: "w" }));
  assert.equal(leanOf(room, "marks"), "B");
  assert.deepEqual([...reached(room)].sort(), ["brief", "debate", "final", "openings"]);
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
  assert.equal(fmtScore(6.25), "6.25");
  assert.equal(fmtScore(2.75), "2.75");
  assert.equal(fmtScore(6.5), "6.5");
  assert.equal(fmtScore(13 / 3), "4.33");
  assert.equal(fmtScore(7), "7.0");
  assert.equal(firstSentence("ROE is 26.75% [P1]. Debt is low."), "ROE is 26.75% [P1].");
  assert.equal(firstSentence("No full stop"), "No full stop");
  assert.equal(fmtScore(null), null);
  assert.equal(fmtElapsed(65.4), "1:05");
  assert.equal(fmtElapsed(null), null);
});

test("spoken lines: tags out, cut at a sentence, one line per turn", () => {
  assert.equal(clip("ROE is 26.75% [P1]. Debt is low [P2]."), "ROE is 26.75%. Debt is low.");
  const long = "One sentence here. " + "word ".repeat(80);
  assert.equal(clip(long, 60), "One sentence here. word word word word word word word word…");
  assert.equal(clip("First part ends here. Second part runs on and on and on.", 40), "First part ends here.");
  const reply = lineOf({ stage: "debate", round: 2, seat: "alwaleed", flags: null, data: { responds_to: "buffett", lean: "B", headline: "Not so.", text: "Debt is 0.20 [P2].", changed: false } });
  assert.deepEqual(reply, { seat: "alwaleed", stage: "debate", kind: "answers", to: "buffett", lean: "B", score: null, text: "Not so. Debt is 0.20." });
  // The final word reads out the position and what changed in it; an open session has no lean.
  const last = lineOf({ stage: "final", round: 3, seat: "marks", flags: null, data: { lean: null, lean_changed: false, text: "I stay here [P1].", changed: "", would_change: "w" } });
  assert.deepEqual(last, { seat: "marks", stage: "final", kind: "finals", to: null, lean: null, score: null, text: "I stay here." });
  assert.equal(lineOf({ stage: "final", round: 3, seat: "marks", flags: null, data: { lean: "A", text: "Here.", changed: "The payout.", would_change: "" } }).text, "Here. The payout.");
  const vote = lineOf({ stage: "vote", round: 3, seat: "marks", flags: null, data: { scores: { A: 3, B: 8 }, top: "B", reason: "Because." } });
  assert.equal(vote.kind, "votes");
  assert.equal(vote.score, 8);
  // The Chair's line: the complete answer in a new session, the summary in a scored one.
  assert.equal(lineOf({ stage: "verdict", round: null, seat: "chair", flags: null, data: { headline: "The room answers", answer: "Here it is." } }).text, "The room answers. Here it is.");
  assert.equal(lineOf({ stage: "verdict", round: null, seat: "chair", flags: null, data: { headline: "Covered", summary: "Most read it so." } }).text, "Covered. Most read it so.");
  assert.equal(lineOf({ stage: "openings", round: 1, seat: "lynch", flags: null, data: { absent: true, error: "busy" } }).kind, "absent");
  assert.equal(lineOf({ stage: "faultlines", round: null, seat: "chair", flags: null, data: { lines: [{ title: "Payout?" }, { title: "Cycle" }], summary: "" } }).text, "Payout. Cycle.");
});

test("a line holds the floor longer for more text, shorter at higher speed", () => {
  assert.equal(lineMs(110, 1), 3_400);
  assert.equal(lineMs(110, 2), 1_700);
  assert.ok(lineMs(300, 1) > lineMs(100, 1));
  assert.equal(lineMs(0, 1), lineMs(20, 1));
});
