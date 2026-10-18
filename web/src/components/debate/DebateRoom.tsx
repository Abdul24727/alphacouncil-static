"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useLocale, useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { Link } from "@/i18n/navigation";
import { ApiError } from "@/lib/api/client";
import { useMe } from "@/lib/auth";
import {
  EMPTY_ROOM,
  STAGES,
  applyEvent,
  reached,
  roomFromSession,
  type DebateEvent,
  type Room,
  type SeatInfo,
  type Stage,
} from "@/lib/debate";
import { DEBATE_KEY, streamDebate, useDebateSession, useDebateSessions, useDebateStatus } from "@/lib/debate-api";
import { fmtDate, fmtStamp } from "@/lib/format";
import { useTickerDetail } from "@/lib/queries";
import { useGroupTicker } from "@/lib/ticker-groups";
import { seatName } from "./parts";
import { OnTheTable, RoundCard, SeatArc, errKey } from "./Stage";
import { KeyPoints, StageView } from "./Transcript";

const PANEL = "rounded-panel border border-line bg-panel p-3";
const BUTTON = "rounded-panel border border-line px-2.5 py-1 text-text-soft hover:border-muted hover:text-text disabled:opacity-50";

/**
 * Advisors' debate room (stock page, Advisors tab): a Pro member puts a question about this
 * stock to simulated advisors, who debate it in rounds; a neutral Chair returns a scored
 * assessment of the data. Streams live; sessions are saved under "Past sessions".
 */
export function DebateRoom() {
  const t = useTranslations("debate");
  const qc = useQueryClient();
  const slug = useGroupTicker(1);
  const status = useDebateStatus();
  const locale = useLocale();
  const detail = useTickerDetail(slug);
  // The session streaming into this page, if any. Otherwise the room shows a saved session.
  const [live, setLive] = useState<Room | null>(null);
  const [picked, setPicked] = useState<Stage | null>(null); // a tab the member opened; null follows the session
  const [openId, setOpenId] = useState<number | null>(null); // a past session the member opened
  const [fresh, setFresh] = useState(false); // "New question": the form, not the session still running
  const [showPast, setShowPast] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const streaming = useRef<AbortController | null>(null);
  useEffect(() => () => streaming.current?.abort(), []);

  // A saved session: one the member opened, or this account's session still running (another
  // tab, a reload, or this page's own after its stream broke), followed until it ends.
  const running = status.data?.running ?? null;
  const shownId = live ? null : (openId ?? (fresh ? null : running));
  const saved = useDebateSession(shownId);
  const room: Room = live ?? (shownId != null && saved.data ? roomFromSession(saved.data) : EMPTY_ROOM);

  const convene = async (question: string, locale: "en" | "ar") => {
    if (!slug) return;
    setStartError(null);
    setPicked(null);
    setOpenId(null);
    setShowPast(false);
    const ctrl = new AbortController();
    streaming.current = ctrl;
    let id: number | null = null;
    let finished = false;
    try {
      await streamDebate(
        { ticker: slug, question, locale },
        (e: DebateEvent) => {
          if (e.type === "session") id = e.session.id;
          if (e.type === "done") finished = true;
          setLive((r) => applyEvent(r ?? EMPTY_ROOM, e));
        },
        ctrl.signal,
      );
    } catch (err) {
      if (ctrl.signal.aborted) return;
      if (id == null) setStartError(err instanceof ApiError ? err.message : "unreachable");
    } finally {
      if (streaming.current === ctrl) streaming.current = null;
      void qc.invalidateQueries({ queryKey: DEBATE_KEY });
    }
    // The stream ended early (network): the session goes on on the server; follow it from there.
    if (id != null && !finished) {
      setLive(null);
      setOpenId(id);
    }
  };

  const openSaved = (id: number) => {
    streaming.current?.abort();
    streaming.current = null;
    setLive(null);
    setShowPast(false);
    setPicked(null);
    setOpenId(id);
    void qc.invalidateQueries({ queryKey: [...DEBATE_KEY, "session", id] });
  };

  const newQuestion = () => {
    if (room.status === "running") return;
    setLive(null);
    setShowPast(false);
    setPicked(null);
    setOpenId(null);
    setFresh(true);
  };

  // A tab or a key-points heading opens that stage below the seats and brings it into view.
  const pick = (stage: Stage) => {
    setPicked(stage);
    requestAnimationFrame(() => document.querySelector("[data-stage-view]")?.scrollIntoView({ behavior: "smooth", block: "start" }));
  };

  // Before a session: the roster, less any seat tied to this company (it sits out, as the API seats it).
  const tickerKey = detail.data?.ticker.ticker_key;
  const roster = (status.data?.seats as SeatInfo[] | undefined) ?? [];
  const sittingOut = room.session ? [] : roster.filter((s) => tickerKey && s.recuse?.includes(tickerKey));
  const seats: SeatInfo[] = room.session?.seats ?? roster.filter((s) => !sittingOut.includes(s));
  const view: Stage | null = picked ?? (room.status === "done" ? "verdict" : room.stage);
  const signedIn = !!status.data?.signed_in;

  return (
    <div className="flex flex-col gap-2.5 p-2.5" data-debate-room>
      <header className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-panel border border-line bg-panel px-3 py-2">
        <h2 className="headline text-[22px] leading-none">{t("title")}</h2>
        {status.data?.stand_in && (
          <span className="label-caps rounded-chip border border-line px-1.5 text-muted" title={t("standInTip")}>
            {t("standIn")}
          </span>
        )}
        <div className="ms-auto flex gap-2 @4xl:order-last">
          {signedIn && (
            <button type="button" className={BUTTON} onClick={() => setShowPast((v) => !v)} aria-expanded={showPast} data-past-toggle>
              {t("past")}
            </button>
          )}
          {room.session && (
            <button type="button" className={BUTTON} onClick={newQuestion} disabled={room.status === "running"} data-new-question>
              {t("newQuestion")}
            </button>
          )}
        </div>
        <StageTabs room={room} view={view} onPick={pick} />
      </header>

      {showPast && <PastSessions onOpen={openSaved} current={room.session?.id ?? null} />}

      {/* Side by side from a mid-size work area; the column is its own container, so the seats
          and the options size to the column, not to the window. */}
      <div className="grid gap-2.5 @3xl:grid-cols-[minmax(0,1fr)_280px]">
        <div className="@container flex min-w-0 flex-col gap-2.5">
          {room.session && <OnTheTable room={room} />}
          <section className={`${PANEL} flex flex-col gap-3`} data-stage>
            <SeatArc seats={seats} room={room.session ? room : null} />
            {sittingOut.length > 0 && (
              <p className="text-center text-[12px] text-muted" data-sits-out>
                {t("sitsOut", { names: sittingOut.map((s) => seatName(s, locale)).join(t("and")), n: sittingOut.length })}
              </p>
            )}
            {room.session ? (
              <RoundCard room={room} />
            ) : shownId != null ? (
              <p className="animate-pulse text-center text-muted">{t("loading")}</p>
            ) : (
              <QuestionForm onConvene={convene} error={startError} />
            )}
          </section>
          {room.session && view && <StageView room={room} stage={view} />}
          {!room.session && shownId == null && <HowItWorks />}
        </div>
        {room.session ? <KeyPoints room={room} onPick={pick} /> : <IdleSide />}
      </div>

      <Disclaimer />
    </div>
  );
}

function StageTabs({ room, view, onPick }: { room: Room; view: Stage | null; onPick: (s: Stage) => void }) {
  const t = useTranslations("debate");
  const open = reached(room);
  return (
    <nav aria-label={t("stagesNav")} className="-mb-2 flex w-full items-stretch overflow-x-auto @4xl:mb-0 @4xl:w-auto">
      {STAGES.map((s) => {
        const live = room.status === "running" && room.stage === s;
        const done = open.has(s) && !live;
        return (
          <button
            key={s}
            type="button"
            disabled={!open.has(s)}
            onClick={() => onPick(s)}
            aria-current={view === s ? "step" : undefined}
            data-stage-tab={s}
            className={`relative flex items-center gap-1.5 px-2.5 py-2 whitespace-nowrap disabled:cursor-default ${
              view === s ? "text-text after:absolute after:inset-x-2 after:bottom-0 after:h-0.5 after:bg-signal" : open.has(s) ? "text-text-soft hover:text-text" : "text-muted/70"
            }`}
          >
            <span
              aria-hidden
              className={`size-1.5 rounded-full ${live ? "animate-pulse bg-signal" : done ? "bg-text-soft" : "border border-muted/60"}`}
            />
            {t(`stages.${s}`)}
          </button>
        );
      })}
    </nav>
  );
}

const SUGGESTIONS = 3;

function QuestionForm({ onConvene, error }: { onConvene: (q: string, locale: "en" | "ar") => void; error: string | null }) {
  const t = useTranslations("debate");
  const locale = useLocale();
  const slug = useGroupTicker(1);
  const detail = useTickerDetail(slug);
  const status = useDebateStatus();
  const me = useMe();
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const ref = detail.data?.ticker;
  const company = ref ? (locale === "ar" ? ref.name_ar ?? ref.name_en : ref.name_en ?? ref.name_ar) ?? ref.symbol : slug ?? "";
  const s = status.data;
  const resets = s ? fmtDate(s.resets_at.slice(0, 10), locale) : null;

  if (status.isPending || me.isPending) return <div className="h-40 animate-pulse rounded-panel bg-panel-raised/40" aria-hidden />;
  if (!s) return <p className="text-loss">{t("errors.advisors_unavailable")}</p>;

  if (!s.signed_in) {
    return (
      <div className="mx-auto flex max-w-[560px] flex-col items-center gap-2 text-center" data-debate-locked="signin">
        <p className="text-text-soft">{t("locked.signIn")}</p>
        <Link href="/login" className="rounded-panel bg-signal px-3 py-1.5 font-semibold text-signal-ink hover:opacity-90">
          {t("locked.signInLink")}
        </Link>
      </div>
    );
  }
  if (s.plan !== "pro") {
    return (
      <div className="mx-auto flex max-w-[560px] flex-col items-start gap-1.5" data-pro-locked data-debate-locked="pro">
        <span className="label-caps rounded-chip border border-signal/50 px-1.5 text-signal">{t("pro")}</span>
        <span className="text-text-soft">{t("locked.lead", { limit: s.pro_limit })}</span>
        <Link href="/pricing" className="text-signal hover:underline">
          {t("locked.seePro")}
        </Link>
      </div>
    );
  }
  const left = s.limit - s.used;
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (q.trim().length < 3 || busy) return;
    setBusy(true);
    try {
      await onConvene(q.trim(), locale === "ar" ? "ar" : "en");
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="mx-auto flex w-full max-w-[640px] flex-col gap-2" data-question-form>
      <label htmlFor="debate-q" className="text-text">
        {t("form.label", { company })}
      </label>
      <textarea
        id="debate-q"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        maxLength={300}
        rows={2}
        dir="auto"
        placeholder={t("form.placeholder")}
        className="resize-none rounded-panel border border-line bg-bg px-2.5 py-2 text-text placeholder:text-muted focus:border-muted"
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            e.currentTarget.form?.requestSubmit();
          }
        }}
      />
      <div className="flex flex-wrap gap-1.5">
        {Array.from({ length: SUGGESTIONS }, (_, i) => t(`form.suggestions.${i}`)).map((x) => (
          <button
            key={x}
            type="button"
            onClick={() => setQ(x)}
            className="rounded-chip border border-line px-2 py-0.5 text-start text-[12px] text-text-soft hover:border-muted hover:text-text"
          >
            {x}
          </button>
        ))}
      </div>
      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-2">
        <button
          type="submit"
          disabled={busy || left <= 0 || q.trim().length < 3}
          className="rounded-panel bg-signal px-3 py-1.5 font-semibold text-signal-ink hover:opacity-90 disabled:opacity-50"
          data-convene
        >
          {busy ? t("form.convening") : t("form.convene")}
        </button>
        <span className="text-muted" data-allowance>
          {t.rich("form.allowance", {
            used: s.used,
            limit: s.limit,
            n: (c) => <span className="num text-text-soft">{c}</span>,
          })}
          {resets && <> · {t("form.resets", { date: resets })}</>}
        </span>
      </div>
      {left <= 0 && <p className="text-text-soft">{t("limitReached", { limit: s.limit, date: resets ?? "" })}</p>}
      {error && <p className="text-loss">{t(`errors.${errKey(error)}`, { code: error })}</p>}
      <p className="text-[12px] text-muted">{t("form.time")}</p>
    </form>
  );
}

function PastSessions({ onOpen, current }: { onOpen: (id: number) => void; current: number | null }) {
  const t = useTranslations("debate");
  const locale = useLocale();
  const list = useDebateSessions(true);
  return (
    <section className={PANEL} data-past-sessions>
      <h3 className="label-caps mb-1 text-muted">{t("past")}</h3>
      {list.isPending ? (
        <div className="h-16 animate-pulse rounded-panel bg-panel-raised/40" aria-hidden />
      ) : !list.data?.length ? (
        <p className="text-muted">{t("pastEmpty")}</p>
      ) : (
        <ul className="flex max-h-[320px] flex-col overflow-y-auto">
          {list.data.map((x) => {
            const result = x.result as { headline?: string | null; best?: string[] } | null;
            return (
              <li key={x.id} className="border-t border-line first:border-t-0">
                <button
                  type="button"
                  onClick={() => onOpen(x.id)}
                  aria-current={x.id === current ? "true" : undefined}
                  className="grid w-full grid-cols-[auto_minmax(0,1fr)] items-baseline gap-x-3 gap-y-0.5 px-1 py-2 text-start hover:bg-panel-raised aria-[current]:bg-panel-raised @3xl:grid-cols-[110px_70px_minmax(0,1fr)_auto]"
                >
                  <span className="num text-[11.5px] text-muted">{fmtStamp(x.created_at, locale)}</span>
                  <span className="num text-[12px] text-text @3xl:order-none">{x.ticker?.symbol ?? x.ticker_key}</span>
                  <span className="col-span-2 truncate text-text-soft @3xl:col-span-1" dir="auto">
                    {result?.headline || x.question}
                  </span>
                  <span className={`label-caps col-span-2 @3xl:col-span-1 ${x.status === "failed" ? "text-loss" : "text-muted"}`}>{t(`status.${x.status}`)}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

const HOW: Stage[] = ["brief", "openings", "faultlines", "debate", "vote", "verdict"];

function HowItWorks() {
  const t = useTranslations("debate");
  return (
    <section className={PANEL} data-how>
      <h3 className="headline text-[20px] leading-none">{t("how.title")}</h3>
      <ol className="mt-2 flex flex-col">
        {HOW.map((s) => (
          <li key={s} className="flex gap-3 border-t border-line py-2 first:border-t-0">
            <span className="label-caps w-24 shrink-0 pt-0.5 text-muted">{t(`stages.${s}`)}</span>
            <span className="text-text-soft">{t(`how.steps.${s}`)}</span>
          </li>
        ))}
      </ol>
      <p className="mt-2 text-[12px] text-muted">{t("how.data")}</p>
    </section>
  );
}

function IdleSide() {
  const t = useTranslations("debate");
  return (
    <aside className={`${PANEL} flex flex-col gap-2 self-start`} aria-label={t("keyPoints")} data-key-points>
      <h3 className="label-caps text-muted">{t("keyPoints")}</h3>
      <p className="text-muted">{t("kpEmpty")}</p>
    </aside>
  );
}

export function Disclaimer() {
  const t = useTranslations("debate");
  return (
    <p className="px-1 text-center text-[11.5px] leading-relaxed text-muted" data-debate-disclaimer>
      {t("disclaimer")}{" "}
      <Link href="/legal/ai-financial-disclaimer" className="text-signal hover:underline">
        {t("disclaimerLink")}
      </Link>
    </p>
  );
}
