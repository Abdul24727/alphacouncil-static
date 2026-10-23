"use client";

import { useTranslations } from "next-intl";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { SPEEDS, lineMs, lineOf, type Line, type Room } from "@/lib/debate";
import { SeatDisc, useSeats } from "./parts";

const subscribeMotion = (cb: () => void) => {
  const m = window.matchMedia("(prefers-reduced-motion: reduce)");
  m.addEventListener("change", cb);
  return () => m.removeEventListener("change", cb);
};
/** Typing and moving seats are off for people who ask for less motion. */
export function useReducedMotion() {
  return useSyncExternalStore(subscribeMotion, () => window.matchMedia("(prefers-reduced-motion: reduce)").matches, () => false);
}

export type Player = {
  line: Line | null;
  index: number;
  waiting: number;
  playing: boolean;
  speed: number;
  cycleSpeed: () => void;
  skip: () => void;
  replay: () => void;
};

/**
 * The turns of a session, one at a time: each answer holds the floor for a moment (longer for more
 * text, shorter at higher speed), then the next. Live sessions play as answers arrive; a saved one
 * opens on its last line, with "Play the debate" to hear it again. Keyed by session in the caller,
 * so a new session starts a new player.
 */
export function useTurnPlayer(room: Room, live: boolean): Player {
  const total = room.turns.length;
  const [index, setIndex] = useState(() => (live ? 0 : Math.max(total - 1, 0)));
  const [playing, setPlaying] = useState(live);
  const [speed, setSpeed] = useState<number>(1.5);
  // When the line on show first appeared: a line that waited for its turn gets its full time.
  const started = useRef<{ index: number; at: number }>({ index: -1, at: 0 });
  const turn = room.turns[index];
  const line = turn ? lineOf(turn) : null;
  const chars = line ? line.text.length : -1;

  useEffect(() => {
    if (!playing || chars < 0) return;
    if (started.current.index !== index) started.current = { index, at: Date.now() };
    if (index >= total - 1) return; // nothing waiting: hold the floor until the next answer lands
    const wait = Math.max(started.current.at + lineMs(chars, speed) - Date.now(), 0);
    const id = setTimeout(() => setIndex((i) => Math.min(i + 1, total - 1)), wait);
    return () => clearTimeout(id);
  }, [playing, index, total, speed, chars]);

  return {
    line,
    index,
    waiting: Math.max(total - 1 - index, 0),
    playing,
    speed,
    cycleSpeed: () => setSpeed((s) => SPEEDS[(SPEEDS.indexOf(s as (typeof SPEEDS)[number]) + 1) % SPEEDS.length]),
    skip: () => setIndex(Math.max(total - 1, 0)),
    replay: () => {
      started.current = { index: -1, at: 0 };
      setIndex(0);
      setPlaying(true);
    },
  };
}

/** The line typed out character by character (all at once with reduced motion). */
function Typed({ text, speed }: { text: string; speed: number }) {
  const reduced = useReducedMotion();
  const [n, setN] = useState(0);
  useEffect(() => {
    if (reduced) return;
    const id = setInterval(() => setN((k) => (k >= text.length ? k : k + 2)), Math.round(36 / speed));
    return () => clearInterval(id);
  }, [text, speed, reduced]);
  const shown = reduced ? text.length : Math.min(n, text.length);
  return (
    <>
      {text.slice(0, shown)}
      {shown < text.length && <span aria-hidden className="ms-0.5 inline-block h-[1em] w-[2px] translate-y-[2px] animate-pulse bg-signal" />}
    </>
  );
}

/** The speech bubble under the seats: who has the floor, what they say, and the playback controls. */
export function SpeechBubble({ room, player }: { room: Room; player: Player }) {
  const t = useTranslations("debate.player");
  const { seat, name, short } = useSeats(room.session?.seats);
  const { line } = player;
  if (!line) return null;
  // An open session has no options, so the caption says what the seat is doing without a lean.
  const action =
    line.kind === "opens"
      ? line.lean
        ? t("opens", { option: line.lean })
        : t("opensPlain")
      : line.kind === "answers"
        ? line.lean
          ? t("answers", { name: short(line.to), option: line.lean })
          : t("answersPlain", { name: short(line.to) })
        : line.kind === "finals"
          ? line.lean
            ? t("finals", { option: line.lean })
            : t("finalsPlain")
          : line.kind === "votes"
            ? t("votes", { option: line.lean ?? "", score: String(line.score ?? "") })
            : t(line.kind);
  const done = room.status !== "running" && player.waiting === 0;

  return (
    <section
      className="mx-auto w-full max-w-[640px] rounded-panel border border-signal/40 bg-panel-raised px-4 py-3"
      aria-live="polite"
      data-speech={line.seat}
    >
      <div className="flex min-w-0 items-center gap-2">
        <SeatDisc seat={seat(line.seat)} size={28} active />
        <span className="truncate font-semibold text-text">{line.seat === "chair" ? t("chair") : name(line.seat)}</span>
        <span className="label-caps shrink-0 text-signal">{action}</span>
      </div>
      {line.text && (
        <p key={player.index} className="mt-1.5 min-h-[3em] text-[14px] leading-relaxed text-text" dir="auto" data-speech-text>
          <Typed text={line.text} speed={player.speed} />
        </p>
      )}
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[12px] text-muted">
        <span data-up-next>{t("upNext", { n: player.waiting })}</span>
        <div className="ms-auto flex items-center gap-1.5">
          <button
            type="button"
            onClick={player.cycleSpeed}
            title={t("speed")}
            className="num rounded-chip border border-line px-1.5 py-0.5 text-text-soft hover:border-muted hover:text-text"
            data-speed
          >
            {player.speed}×
          </button>
          {player.waiting > 0 && (
            <button type="button" onClick={player.skip} className="rounded-chip border border-line px-2 py-0.5 text-text-soft hover:border-muted hover:text-text" data-skip>
              {t("skip")}
            </button>
          )}
          {done && (
            <button type="button" onClick={player.replay} className="rounded-chip border border-line px-2 py-0.5 text-text-soft hover:border-muted hover:text-text" data-replay>
              {t("replay")}
            </button>
          )}
        </div>
      </div>
    </section>
  );
}
