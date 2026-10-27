"use client";

import Image from "next/image";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import {
  briefOf,
  finalOf,
  fmtElapsed,
  fmtScore,
  leanOf,
  modeOf,
  progress,
  voteOf,
  type Room,
  type SeatInfo,
} from "@/lib/debate";
import { OptionId, SeatDisc, WritingMark, seatLens, seatName, seatShort, useSeats } from "./parts";

/**
 * The room: the advisors standing round a table, the Chair at its head. Seats nearer the middle sit
 * higher, as round a table seen from the front, and the table's edge passes in front of them so they
 * stand at it rather than float above it. Logical positions, so the order runs right to left in Arabic.
 *
 * Built to the owner's reference (2026-10-26) within BRAND.md, which wins where they disagree
 * (Step 22's own default). Dropped from the reference: the warm cove glow behind the panels, the
 * backlit wall and the soft gradients on the table, all of which BRAND.md bans outright. Kept: the
 * graphite room, the curved table, the arc of seats, the wall mark behind them, orange only where it
 * carries meaning — here the seat that has the floor.
 *
 * Three passes, because the table has to sit between the busts and their names: busts, then the
 * table, then the names on it. They share one `seatX` so the columns line up.
 */
export function SeatArc({
  seats,
  room,
  speaking = null,
  addressee = null,
}: {
  seats: SeatInfo[];
  room: Room | null;
  /** The seat whose line is on the floor (Player.tsx), and the advisor it answers. */
  speaking?: string | null;
  addressee?: string | null;
}) {
  const t = useTranslations("debate");
  const locale = useLocale();
  const advisors = seats.filter((s) => s.role === "advisor");
  const chair = seats.find((s) => s.role === "chair");
  const order = [...advisors];
  if (chair) order.splice(Math.floor(advisors.length / 2), 0, chair);
  const n = order.length;
  // Six seats and the Chair need a narrower column each, or the names touch on a phone.
  const crowded = n > 5;
  // Across the arc, and how high this seat sits: 0 at the ends, 1 at the head.
  const seatX = (i: number, inset: number) => `${(inset + (100 - 2 * inset) * (i / Math.max(n - 1, 1))).toFixed(2)}%`;
  const lift = (i: number) => Math.sin(Math.PI * (i / Math.max(n - 1, 1)));
  const state = (s: SeatInfo) => ({
    writing: !!room?.writing.includes(s.id),
    speaks: speaking === s.id,
    addressed: addressee === s.id,
  });
  const dim = (s: SeatInfo) => {
    const { writing, speaks, addressed } = state(s);
    return speaking && !speaks && !addressed && !writing ? "opacity-50" : "";
  };
  const COL =
    "absolute -translate-x-1/2 [inset-inline-start:var(--x-sm)] [top:var(--y-sm)] rtl:translate-x-1/2 " +
    "@3xl:[inset-inline-start:var(--x-lg)] @3xl:[top:var(--y-lg)]";
  /** Where a seat sits: across the arc, and how far down at each size. */
  const place = (i: number, smallTop: number, largeTop: number, smallDrop: number, largeDrop: number) =>
    ({
      "--x-sm": seatX(i, crowded ? 7 : 12),
      "--x-lg": seatX(i, 7),
      "--y-sm": `${Math.round(smallTop - smallDrop * lift(i))}px`,
      "--y-lg": `${Math.round(largeTop - largeDrop * lift(i))}px`,
    }) as React.CSSProperties;

  return (
    <div className="relative h-[242px] overflow-x-clip @3xl:h-[350px]" role="list" aria-label={t("seatsLabel")}>
      {/* The wall behind the room: the brand mark, quiet, never competing with the seats. */}
      <span aria-hidden className="absolute inset-x-0 top-2 flex items-center justify-center gap-1.5 opacity-25 @3xl:top-4">
        <span className="block size-2 rounded-[2px] bg-signal @3xl:size-2.5" />
        <span className="headline text-[13px] leading-none tracking-tight text-text @3xl:text-[16px]">AlphaCouncil</span>
      </span>

      {/* 1. The busts, standing behind the table. */}
      {order.map((s, i) => {
        const { writing, speaks } = state(s);
        return (
          <div
            key={s.id}
            role="listitem"
            data-seat={s.id}
            data-writing={writing || undefined}
            data-speaking={speaks || undefined}
            className={`${COL} z-0 flex flex-col items-center transition-opacity duration-300 ${dim(s)} ${
              crowded ? "w-[64px] @3xl:w-[168px]" : "w-[86px] @3xl:w-[190px]"
            }`}
            style={place(i, 62, 44, 30, 40)}
          >
            {speaks ? <SpeakingBars /> : <WritingMark on={writing} />}
            <span
              className={`transition-transform duration-300 motion-reduce:transition-none ${speaks ? "-translate-y-1 scale-105" : ""}`}
            >
              <SeatBust seat={s} active={writing || speaks} speaking={speaks} crowded={crowded} />
            </span>
          </div>
        );
      })}

      {/* 2. The table, in front of the busts. A flat graphite surface with one lit edge — no gradient. */}
      <div
        aria-hidden
        className="absolute inset-x-[-14%] bottom-0 z-10 h-[106px] rounded-t-[50%] border-t border-line bg-panel-raised @3xl:h-[150px]"
      />

      {/* 3. The names, printed on the table. */}
      {order.map((s, i) => {
        const { speaks, addressed } = state(s);
        const lean = room ? leanOf(room, s.id) : null;
        // A scored session shows the seat's top option and score; a new one, that it has had its final word.
        const vote = room ? voteOf(room, s.id) : null;
        const final = room ? finalOf(room, s.id) : null;
        return (
          <div
            key={s.id}
            className={`${COL} z-20 flex flex-col items-center gap-0.5 transition-opacity duration-300 ${dim(s)} ${
              crowded ? "w-[50px] @3xl:w-[104px]" : "w-[76px] @3xl:w-[128px]"
            }`}
            style={place(i, 142, 206, 14, 14)}
          >
            <span
              className={`max-w-full truncate rounded-chip border px-1 py-px text-center text-[9.5px] leading-[1.25] @3xl:overflow-visible @3xl:text-clip @3xl:whitespace-normal @3xl:text-balance @3xl:px-1.5 @3xl:text-[11.5px] ${
                speaks
                  ? "border-signal bg-signal text-signal-ink"
                  : addressed
                    ? "border-dashed border-signal/70 bg-panel text-text"
                    : "border-line bg-panel text-text"
              }`}
            >
              {/* Seven full names do not fit across a phone, so the surname carries it there. */}
              <span className="@3xl:hidden">{s.role === "chair" ? t("chairShort") : seatShort(s, locale)}</span>
              <span className="hidden @3xl:inline">{s.role === "chair" ? t("chair") : seatName(s, locale)}</span>
            </span>
            <span className="hidden max-w-full text-balance text-center text-[10.5px] leading-tight text-muted @3xl:line-clamp-2 @3xl:block">
              {seatLens(s, locale)}
            </span>
            {s.role === "advisor" && (vote || lean || final) && (
              <span className="num text-[11px] text-text-soft" title={vote ? t("topVote") : final ? t("finalWord") : t("leaning")}>
                {vote ? `${vote.top} · ${vote.scores[vote.top]}` : lean ? `→ ${lean}` : "✓"}
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

/**
 * One advisor as a bust: the portrait large and bottom-aligned, so the table's edge crosses the chest.
 * A portrait that is missing or fails to load falls back to the seat's initials, as the discs do.
 */
function SeatBust({
  seat,
  active,
  speaking,
  crowded,
}: {
  seat: SeatInfo;
  active: boolean;
  speaking: boolean;
  crowded: boolean;
}) {
  const [failed, setFailed] = useState<string | null>(null);
  const portrait = seat.portrait && seat.portrait !== failed ? seat.portrait : null;
  // Static classes both ways: Tailwind cannot see a width built from a variable.
  const box = crowded ? "h-[74px] @3xl:h-[182px]" : "h-[86px] @3xl:h-[200px]";
  const wide = crowded ? "w-[64px] @3xl:w-[168px]" : "w-[86px] @3xl:w-[190px]";
  if (!portrait) {
    return (
      <span className={`flex items-end justify-center ${box}`}>
        <SeatDisc seat={seat} size={crowded ? 52 : 60} active={active} />
      </span>
    );
  }
  return (
    <span className={`flex items-end justify-center ${box}`}>
      <Image
        src={portrait}
        alt=""
        width={512}
        height={512}
        sizes="(min-width: 768px) 160px, 88px"
        className={`${wide} h-full object-contain object-bottom ${speaking ? "" : "grayscale-[20%]"}`}
        onError={() => setFailed(portrait)}
      />
    </span>
  );
}

/** Level bars over the seat that has the floor (still bars with reduced motion). */
function SpeakingBars() {
  const t = useTranslations("debate.player");
  return (
    <span className="flex h-4 items-end gap-[2px] px-1" title={t("speaking")} data-speaking-bars>
      {[0, 180, 90].map((delay) => (
        <span
          key={delay}
          aria-hidden
          className="h-3 w-[3px] origin-bottom rounded-[1px] bg-signal animate-speak motion-reduce:animate-none"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </span>
  );
}

/** Seconds since `from`, ticking while `live`. */
function useElapsed(from: string | null | undefined, live: boolean, fixed: number | null) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!live) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [live]);
  if (!live) return fixed;
  return from ? (now - new Date(from).getTime()) / 1000 : null;
}

/** Round N of M, what is happening, who is weighing what, and how far along it is. */
export function RoundCard({ room }: { room: Room }) {
  const t = useTranslations("debate");
  const s = room.session!;
  const { name } = useSeats(s.seats);
  const live = room.status === "running";
  const elapsed = useElapsed(s.created_at, live, room.seconds ?? s.seconds);
  const stage = room.stage ?? "brief";
  const brief = briefOf(room);
  const writers = room.writing.filter((id) => id !== "chair");
  const [tick, setTick] = useState(0);
  useEffect(() => {
    if (writers.length < 2) return;
    const id = setInterval(() => setTick((n) => n + 1), 3500);
    return () => clearInterval(id);
  }, [writers.length]);
  const weigher = writers.length ? writers[tick % writers.length] : null;
  const what = weigher ? brief?.weighing?.[weigher] || "" : "";
  const isRound = stage === "openings" || stage === "debate" || stage === "final" || stage === "vote";
  const state = room.status === "done" ? "done" : room.status === "failed" ? "failed" : stage;

  return (
    <section className="mx-auto w-full max-w-[640px] rounded-panel border border-line bg-panel px-4 py-3" data-round-card data-room-status={room.status} aria-live="polite">
      <div className="flex items-center gap-2">
        <span aria-hidden className={`size-1.5 rounded-full ${live ? "animate-pulse bg-signal" : "bg-muted"}`} />
        <span className="label-caps text-muted">
          {room.status !== "running"
            ? t(`state.${state}`)
            : isRound && room.round
              ? t("roundOf", { n: room.round, m: s.rounds })
              : t("chairStep")}
          {room.status === "running" && <> · {t(`stages.${stage}`)}</>}
        </span>
        {elapsed != null && <span className="num ms-auto text-[12px] text-muted">{fmtElapsed(elapsed)}</span>}
      </div>
      <p className="headline mt-1.5 text-[18px] leading-snug">{t(`happening.${state}`, { error: room.error ? t(`errors.${errKey(room.error)}`) : "" })}</p>
      {room.status === "running" && <p className="mt-1 text-text-soft">{t(`detail.${stage}`)}</p>}
      {room.status === "running" && weigher && what && (
        <p className="mt-1.5 text-text-soft" data-weighing={weigher}>
          {t.rich("weighing", { name: name(weigher), what, b: (c) => <strong className="font-semibold text-text">{c}</strong> })}
        </p>
      )}
      <div className="mt-2.5 h-1 overflow-hidden rounded-full bg-line" role="progressbar" aria-label={t("progress")} aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(progress(room) * 100)}>
        <div className={`h-full ${room.status === "failed" ? "bg-loss" : "bg-signal"}`} style={{ width: `${Math.round(progress(room) * 100)}%` }} />
      </div>
    </section>
  );
}

export const ERROR_CODES = [
  "credentials",
  "busy",
  "timeout",
  "unreachable",
  "no_credit",
  "bad_output",
  "cut_off",
  "too_few",
  "internal",
  "interrupted",
  "debate_limit",
  "debate_running",
  "pro_required",
  "advisors_unavailable",
] as const;
export const errKey = (code: string) => ((ERROR_CODES as readonly string[]).includes(code) ? code : "unknown");

/** The question as the Chair framed it, and the options with who leans where or, after the vote, their scores. */
export function OnTheTable({ room, onStock }: { room: Room; onStock?: React.ReactNode }) {
  const t = useTranslations("debate");
  const locale = useLocale();
  const s = room.session!;
  const { short } = useSeats(s.seats);
  const brief = briefOf(room);
  const result = room.result;
  const advisors = s.seats.filter((x) => x.role === "advisor");
  const company = s.ticker ? (locale === "ar" ? s.ticker.name_ar ?? s.ticker.name_en : s.ticker.name_en ?? s.ticker.name_ar) : null;

  return (
    <section className="grid gap-x-6 gap-y-3 rounded-panel border border-line bg-panel p-3 @4xl:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]" data-on-table>
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="label-caps text-muted">{t("onTable")}</span>
          {s.ticker && (
            <span className="flex items-center gap-1.5 rounded-chip border border-line px-1.5">
              <span className="num text-[11px]">{s.ticker.symbol}</span>
              {company && <span className="text-[12px] text-text-soft">{company}</span>}
            </span>
          )}
          {onStock}
        </div>
        <h3 className="headline mt-1.5 text-[20px] leading-snug" dir="auto">
          {brief?.question ?? s.question}
        </h3>
        {brief && (
          <p className="mt-1 text-muted" dir="auto">
            {t("youAsked", { question: s.question })}
          </p>
        )}
      </div>
      {/* A choice session lists the readings on the table; an open one, what the room must weigh. */}
      {brief && modeOf(room) === "open" ? (
        <div className="min-w-0">
          <p className="label-caps mb-1 text-muted">{t("focus")}</p>
          <ul className="flex flex-col" aria-label={t("focus")} data-focus-list>
            {brief.focus.map((f) => (
              <li key={f} className="border-t border-line py-1.5 first:border-t-0" dir="auto">
                {f}
              </li>
            ))}
            {!brief.focus.length && <li className="py-1.5 text-muted">{t("noOptions")}</li>}
          </ul>
        </div>
      ) : (
        <ol className="flex flex-col" aria-label={t("options")}>
          {(brief?.options ?? []).map((o) => {
            // Scored sessions show the average; new ones, how many advisors ended up leaning here.
            const avg = result?.average?.[o.id] ?? null;
            const best = !!result?.best?.includes(o.id);
            const tally = result?.mode === "choice" ? (result.tally?.[o.id] ?? 0) : null;
            const leaning = advisors.filter((a) => leanOf(room, a.id) === o.id).map((a) => short(a.id));
            return (
              <li key={o.id} className="flex items-center gap-2.5 border-t border-line py-1.5 first:border-t-0" data-option={o.id}>
                <OptionId id={o.id} strong={best} />
                <span className="min-w-0 flex-1" dir="auto">
                  {o.label}
                </span>
                {tally != null ? (
                  <span className="flex w-[118px] shrink-0 items-center gap-2" title={t("finalLeans")} data-tally={tally}>
                    <span className="h-1 flex-1 overflow-hidden rounded-full bg-line">
                      <span
                        className={`block h-full ${best ? "bg-signal" : "bg-neutral-seat"}`}
                        style={{ width: `${result!.voters ? (tally / result!.voters) * 100 : 0}%` }}
                      />
                    </span>
                    <span className={`num w-10 text-end text-[13px] ${best ? "text-text" : "text-text-soft"}`}>
                      {t("ofN", { n: tally, m: result!.voters })}
                    </span>
                  </span>
                ) : avg != null ? (
                  <span className="flex w-[118px] shrink-0 items-center gap-2" title={t("averageScore")}>
                    <span className="h-1 flex-1 overflow-hidden rounded-full bg-line">
                      <span className={`block h-full ${best ? "bg-signal" : "bg-neutral-seat"}`} style={{ width: `${avg * 10}%` }} />
                    </span>
                    <span className={`num w-8 text-end text-[13px] ${best ? "text-text" : "text-text-soft"}`}>{fmtScore(avg) ?? "—"}</span>
                  </span>
                ) : (
                  leaning.length > 0 && (
                    <span className="shrink-0 truncate text-[12px] text-muted" title={t("leaning")}>
                      {leaning.join(" · ")}
                    </span>
                  )
                )}
              </li>
            );
          })}
          {!brief && <li className="h-16 animate-pulse rounded-panel bg-panel-raised/50" aria-hidden />}
        </ol>
      )}
    </section>
  );
}
