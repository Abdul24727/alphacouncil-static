"use client";

import { useLocale, useTranslations } from "next-intl";
import { useEffect, useState } from "react";
import {
  briefOf,
  fmtElapsed,
  fmtScore,
  leanOf,
  progress,
  voteOf,
  type Room,
  type SeatInfo,
} from "@/lib/debate";
import { OptionId, SeatDisc, WritingMark, seatLens, seatShort, useSeats } from "./parts";

/**
 * The advisors in a semicircle, the Chair at its head. Seats further from the ends sit higher,
 * as round a table seen from the front. Logical positions (inset-inline-start), so the order
 * runs right to left in Arabic.
 */
export function SeatArc({ seats, room }: { seats: SeatInfo[]; room: Room | null }) {
  const t = useTranslations("debate");
  const locale = useLocale();
  const advisors = seats.filter((s) => s.role === "advisor");
  const chair = seats.find((s) => s.role === "chair");
  const order = [...advisors];
  if (chair) order.splice(Math.floor(advisors.length / 2), 0, chair);
  const n = order.length;

  return (
    <div className="relative h-[200px] overflow-x-clip @3xl:h-[232px]" role="list" aria-label={t("seatsLabel")}>
      {order.map((s, i) => {
        const angle = Math.PI * (1.1 + (0.8 * i) / Math.max(n - 1, 1));
        // Narrower spread on phones, so the end seats' name tags stay on screen.
        const x = (r: number) => `${(50 + r * Math.cos(angle)).toFixed(2)}%`;
        const lift = -Math.sin(angle); // 0 at the ends, 1 at the head
        const writing = !!room?.writing.includes(s.id);
        const lean = room ? leanOf(room, s.id) : null;
        const vote = room ? voteOf(room, s.id) : null;
        return (
          <div
            key={s.id}
            role="listitem"
            data-seat={s.id}
            data-writing={writing || undefined}
            className="absolute flex w-[84px] -translate-x-1/2 flex-col items-center gap-1 [inset-inline-start:var(--x-sm)] rtl:translate-x-1/2 @3xl:w-[120px] @3xl:[inset-inline-start:var(--x-lg)]"
            style={{ "--x-sm": x(37), "--x-lg": x(42), top: `${Math.round(78 - 64 * lift)}px` } as React.CSSProperties}
          >
            <WritingMark on={writing} />
            <span className="@3xl:hidden">
              <SeatDisc seat={s} size={s.role === "chair" ? 46 : 52} active={writing} />
            </span>
            <span className="hidden @3xl:block">
              <SeatDisc seat={s} size={s.role === "chair" ? 56 : 66} active={writing} />
            </span>
            <span className="max-w-full truncate rounded-chip border border-line bg-panel px-1.5 py-px text-[12px] text-text">
              {s.role === "chair" ? t("chair") : seatShort(s, locale)}
            </span>
            <span className="hidden max-w-full truncate text-center text-[11px] leading-tight text-muted @3xl:block">{seatLens(s, locale)}</span>
            {s.role === "advisor" && (vote || lean) && (
              <span className="num text-[11px] text-text-soft" title={vote ? t("topVote") : t("leaning")}>
                {vote ? `${vote.top} · ${vote.scores[vote.top]}` : `→ ${lean}`}
              </span>
            )}
          </div>
        );
      })}
    </div>
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
  const isRound = stage === "openings" || stage === "debate" || stage === "vote";
  const state = room.status === "done" ? "done" : room.status === "failed" ? "failed" : stage;

  return (
    <section className="mx-auto w-full max-w-[640px] rounded-panel border border-line bg-panel px-4 py-3" data-round-card aria-live="polite">
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
      <ol className="flex flex-col" aria-label={t("options")}>
        {(brief?.options ?? []).map((o) => {
          const avg = result?.average[o.id] ?? null;
          const best = !!result?.best.includes(o.id);
          const leaning = advisors.filter((a) => leanOf(room, a.id) === o.id).map((a) => short(a.id));
          return (
            <li key={o.id} className="flex items-center gap-2.5 border-t border-line py-1.5 first:border-t-0" data-option={o.id}>
              <OptionId id={o.id} strong={best} />
              <span className="min-w-0 flex-1" dir="auto">
                {o.label}
              </span>
              {result ? (
                <span className="flex w-[118px] shrink-0 items-center gap-2" title={t("averageScore")}>
                  <span className="h-1 flex-1 overflow-hidden rounded-full bg-line">
                    <span className={`block h-full ${best ? "bg-signal" : "bg-neutral-seat"}`} style={{ width: `${(avg ?? 0) * 10}%` }} />
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
    </section>
  );
}
