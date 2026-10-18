"use client";

import { useLocale, useTranslations } from "next-intl";
import {
  briefOf,
  fmtElapsed,
  fmtScore,
  isAbsent,
  turnsOf,
  verdictOf,
  type FaultLines,
  type Reply,
  type Room,
  type Stage,
  type Turn,
  type Vote,
} from "@/lib/debate";
import { DebateText, FlagNotes, OptionId, SeatDisc, useSeats } from "./parts";
import { errKey } from "./Stage";

const PANEL = "rounded-panel border border-line bg-panel p-3";

/** The chosen stage in full: what each seat wrote, with citations and the checks' notes. */
export function StageView({ room, stage }: { room: Room; stage: Stage }) {
  const t = useTranslations("debate");
  const s = room.session!;
  const turns = turnsOf(room, stage);
  const rounds = [...new Set(turns.map((x) => x.round))];
  const waiting = room.status === "running" && room.stage === stage;

  return (
    <section className={PANEL} data-stage-view={stage}>
      <h3 className="headline text-[20px] leading-none">{t(`stages.${stage}`)}</h3>
      {stage === "brief" && <BriefView room={room} />}
      {(stage === "openings" || stage === "debate") &&
        rounds.map((r) => (
          <div key={String(r)} className="mt-2">
            {stage === "debate" && s.rounds > 3 && <p className="label-caps mb-1 text-muted">{t("roundOf", { n: r ?? 0, m: s.rounds })}</p>}
            <ul className="flex flex-col">
              {turns
                .filter((x) => x.round === r)
                .map((x) => (
                  <SpeechItem key={x.seat} room={room} turn={x} />
                ))}
            </ul>
          </div>
        ))}
      {stage === "faultlines" && <FaultLinesView room={room} />}
      {stage === "vote" && <VoteTable room={room} />}
      {stage === "verdict" && <VerdictView room={room} />}
      {waiting && stage !== "verdict" && <p className="mt-2 animate-pulse text-muted">{t("inProgress")}</p>}
      {!turns.length && !waiting && <p className="mt-2 text-muted">{t("notYet")}</p>}
    </section>
  );
}

function BriefView({ room }: { room: Room }) {
  const t = useTranslations("debate");
  const brief = briefOf(room);
  const { name } = useSeats(room.session!.seats);
  const turn = turnsOf(room, "brief")[0];
  if (!brief) return null;
  return (
    <div className="mt-2 flex flex-col gap-3">
      <DebateText text={brief.question} flags={turn?.flags} sources={room.session!.sources} className="text-[15px] text-text" />
      <ol className="flex flex-col gap-1.5">
        {brief.options.map((o) => (
          <li key={o.id} className="flex gap-2">
            <OptionId id={o.id} />
            <div className="min-w-0">
              <p className="text-text" dir="auto">
                {o.label}
              </p>
              {o.detail && <DebateText text={o.detail} flags={turn?.flags} sources={room.session!.sources} className="text-muted" />}
            </div>
          </li>
        ))}
      </ol>
      {brief.focus.length > 0 && (
        <div>
          <p className="label-caps mb-1 text-muted">{t("focus")}</p>
          <ul className="flex list-disc flex-col gap-0.5 ps-4 marker:text-muted" dir="auto">
            {brief.focus.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </div>
      )}
      {Object.values(brief.weighing).some(Boolean) && (
        <div>
          <p className="label-caps mb-1 text-muted">{t("whoWeighs")}</p>
          <ul className="flex flex-col gap-0.5">
            {Object.entries(brief.weighing)
              .filter(([, w]) => w)
              .map(([id, w]) => (
                <li key={id} dir="auto">
                  <span className="text-text">{name(id)}</span> <span className="text-text-soft">{w}</span>
                </li>
              ))}
          </ul>
        </div>
      )}
      {brief.note && (
        <p className="border-s-2 border-line ps-2 text-text-soft" dir="auto">
          {brief.note}
        </p>
      )}
      <FlagNotes flags={turn?.flags} />
    </div>
  );
}

function SpeechItem({ room, turn }: { room: Room; turn: Turn }) {
  const t = useTranslations("debate");
  const { seat, name, short } = useSeats(room.session!.seats);
  const d = turn.data as unknown as Reply;
  return (
    <li className="flex gap-3 border-t border-line py-2.5 first:border-t-0" data-turn={`${turn.stage}:${turn.seat}`}>
      <SeatDisc seat={seat(turn.seat)} size={36} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-2">
          <span className="font-semibold text-text">{name(turn.seat)}</span>
          {d.responds_to && <span className="text-muted">{t("answers", { other: short(d.responds_to) })}</span>}
          {!isAbsent(turn.data) && (
            <span className="num text-[11px] text-text-soft">
              {d.changed ? t("changed", { option: d.lean }) : t("leans", { option: d.lean })}
            </span>
          )}
        </div>
        {isAbsent(turn.data) ? (
          <p className="text-muted">{t("noAnswer", { reason: t(`errors.${errKey(String(turn.data.error))}`) })}</p>
        ) : (
          <>
            {d.headline && (
              <p className="mt-0.5 text-text" dir="auto">
                {d.headline}
              </p>
            )}
            <DebateText text={d.text} flags={turn.flags} sources={room.session!.sources} className="mt-1 text-text-soft" />
            <FlagNotes flags={turn.flags} />
          </>
        )}
      </div>
    </li>
  );
}

function FaultLinesView({ room }: { room: Room }) {
  const t = useTranslations("debate");
  const { short } = useSeats(room.session!.seats);
  const turn = turnsOf(room, "faultlines")[0];
  if (!turn) return null;
  const d = turn.data as unknown as FaultLines;
  return (
    <div className="mt-2 flex flex-col">
      {d.lines.map((f, i) => (
        <div key={i} className="border-t border-line py-2 first:border-t-0">
          <p className="font-semibold text-text" dir="auto">
            {f.title}
          </p>
          {f.between.length > 0 && <p className="text-[12px] text-muted">{f.between.map((x) => short(x)).join(t("versus"))}</p>}
          <DebateText text={f.text} flags={turn.flags} sources={room.session!.sources} className="mt-0.5 text-text-soft" />
        </div>
      ))}
      {d.summary && <DebateText text={d.summary} flags={turn.flags} sources={room.session!.sources} className="mt-1 text-text" />}
      <FlagNotes flags={turn.flags} />
    </div>
  );
}

/** Each advisor's score for each option, and the room's average (computed by the API). */
function VoteTable({ room, caption }: { room: Room; caption?: string }) {
  const t = useTranslations("debate");
  const { seat, name } = useSeats(room.session!.seats);
  const brief = briefOf(room);
  const votes = turnsOf(room, "vote");
  if (!brief || !votes.length) return null;
  const options = brief.options.map((o) => o.id);
  return (
    <div className="mt-2 overflow-x-auto">
      <table className="w-full text-[12.5px]" data-vote-table>
        {caption && <caption className="label-caps mb-1 text-start text-muted">{caption}</caption>}
        <thead>
          <tr className="label-caps text-muted">
            <th className="py-1 pe-2 text-start font-normal">{t("advisor")}</th>
            {options.map((o) => (
              <th key={o} className="num px-2 py-1 text-end font-normal">
                {o}
              </th>
            ))}
            <th className="hidden py-1 ps-3 text-start font-normal @3xl:table-cell">{t("why")}</th>
          </tr>
        </thead>
        <tbody>
          {votes.map((v) => {
            const d = v.data as unknown as Vote;
            return (
              <tr key={v.seat} className="border-t border-line align-top">
                <td className="py-1.5 pe-2">
                  <span className="flex items-center gap-2">
                    <SeatDisc seat={seat(v.seat)} size={22} />
                    <span className="text-text">{name(v.seat)}</span>
                  </span>
                </td>
                {options.map((o) => (
                  <td key={o} className={`num px-2 py-1.5 text-end ${!isAbsent(v.data) && d.top === o ? "text-signal" : "text-text-soft"}`}>
                    {isAbsent(v.data) ? "—" : d.scores[o]}
                  </td>
                ))}
                <td className="hidden py-1.5 ps-3 text-text-soft @3xl:table-cell" dir="auto">
                  {isAbsent(v.data) ? "" : d.reason}
                </td>
              </tr>
            );
          })}
          {room.result && (
            <tr className="border-t border-line">
              <td className="py-1.5 pe-2 text-muted">{t("average")}</td>
              {options.map((o) => (
                <td key={o} className={`num px-2 py-1.5 text-end ${room.result!.best.includes(o) ? "text-text" : "text-muted"}`}>
                  {fmtScore(room.result!.average[o]) ?? "—"}
                </td>
              ))}
              <td className="hidden @3xl:table-cell" />
            </tr>
          )}
        </tbody>
      </table>
      <p className="mt-1.5 text-[11.5px] text-muted">{t("scoresNote")}</p>
    </div>
  );
}

/** The Chair's verdict: the room's assessment, the scores, why, what to watch, the gaps. */
export function VerdictView({ room }: { room: Room }) {
  const t = useTranslations("debate");
  const locale = useLocale();
  const s = room.session!;
  const { seat, name } = useSeats(s.seats);
  const v = verdictOf(room);
  const turn = turnsOf(room, "verdict")[0];
  const brief = briefOf(room);
  const r = room.result;
  if (!v || !brief) return null;
  const label = (id: string) => brief.options.find((o) => o.id === id)?.label ?? id;
  const credited = (c: { seat: string | null; point: string }, i: number) => (
    <li key={i} className="flex gap-2">
      {c.seat ? <SeatDisc seat={seat(c.seat)} size={22} /> : <span className="w-[22px] shrink-0" />}
      <div className="min-w-0">
        {c.seat && <span className="me-1.5 font-semibold text-text">{name(c.seat)}</span>}
        <DebateText text={c.point} flags={turn?.flags} sources={s.sources} className="inline text-text-soft [&>p]:inline" />
      </div>
    </li>
  );

  return (
    <div className="mt-2 flex flex-col gap-4" data-verdict>
      <div className="border-s-2 border-signal ps-3">
        <p className="label-caps text-muted">{t("verdictLabel")}</p>
        <p className="headline mt-1 text-[24px] leading-tight" dir="auto">
          {v.headline}
        </p>
        {v.summary && <DebateText text={v.summary} flags={turn?.flags} sources={s.sources} className="mt-1.5 text-[14px] text-text" />}
      </div>

      {r && (
        <div>
          <p className="label-caps mb-1 text-muted">{t("scores")}</p>
          <ul className="flex flex-col">
            {brief.options.map((o) => {
              const best = r.best.includes(o.id);
              return (
                <li key={o.id} className="flex items-center gap-2.5 border-t border-line py-1.5 first:border-t-0">
                  <OptionId id={o.id} strong={best} />
                  <span className="min-w-0 flex-1" dir="auto">
                    {o.label}
                  </span>
                  <span className="h-1 w-24 overflow-hidden rounded-full bg-line">
                    <span className={`block h-full ${best ? "bg-signal" : "bg-neutral-seat"}`} style={{ width: `${(r.average[o.id] ?? 0) * 10}%` }} />
                  </span>
                  <span className="num w-8 text-end">{fmtScore(r.average[o.id]) ?? "—"}</span>
                </li>
              );
            })}
          </ul>
          <p className="mt-1 text-text-soft">
            {r.best.length > 1
              ? t("tie", { options: r.best.map(label).join(t("and")) })
              : r.best.length === 1
                ? t("agreement", { n: r.agreement, m: r.voters, option: r.best[0] })
                : null}
          </p>
        </div>
      )}

      <div className="grid gap-4 @4xl:grid-cols-2">
        {v.why.length > 0 && (
          <div>
            <p className="label-caps mb-1.5 text-muted">{t("why")}</p>
            <ul className="flex flex-col gap-1.5">{v.why.map(credited)}</ul>
          </div>
        )}
        {v.watch_out && (
          <div>
            <p className="label-caps mb-1.5 text-muted">{t("watchOut")}</p>
            <ul className="flex flex-col gap-1.5">{credited(v.watch_out, 0)}</ul>
          </div>
        )}
        {v.disagreements.length > 0 && (
          <div>
            <p className="label-caps mb-1.5 text-muted">{t("disagree")}</p>
            <ul className="flex list-disc flex-col gap-1 ps-4 text-text-soft marker:text-muted" dir="auto">
              {v.disagreements.map((x, i) => (
                <li key={i}>
                  <DebateText text={x} flags={turn?.flags} sources={s.sources} className="inline [&>p]:inline" />
                </li>
              ))}
            </ul>
          </div>
        )}
        {v.gaps.length > 0 && (
          <div>
            <p className="label-caps mb-1.5 text-muted">{t("gaps")}</p>
            <ul className="flex list-disc flex-col gap-1 ps-4 text-text-soft marker:text-muted" dir="auto">
              {v.gaps.map((x, i) => (
                <li key={i}>{x}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
      <FlagNotes flags={turn?.flags} />

      <VoteTable room={room} caption={t("howScored")} />

      <div className="flex flex-col gap-1 border-t border-line pt-2 text-[12px] text-muted">
        <p>{t("notAdvice")}</p>
        {s.sources && (
          <p>
            <span className="me-1">{t("dataRead")}</span>
            {Object.entries(s.sources).map(([tag, src], i) => (
              <span key={tag}>
                {i > 0 && " · "}
                <span className="label-caps me-1">{tag}</span>
                {locale === "ar" ? src.title_ar : src.title_en}
              </span>
            ))}
          </p>
        )}
        <p>
          {room.seconds != null && <>{t("took", { time: fmtElapsed(room.seconds) ?? "" })} · </>}
          {t("models", { advisors: s.models.advisors ?? "", chair: s.models.chair ?? "" })}
        </p>
      </div>
    </div>
  );
}

/** Running notes down the side: one line per seat per step, in order; a heading opens that stage. */
export function KeyPoints({ room, onPick }: { room: Room; onPick: (stage: Stage) => void }) {
  const t = useTranslations("debate");
  const { short } = useSeats(room.session?.seats);
  const s = room.session;
  const brief = briefOf(room);
  const verdict = verdictOf(room);

  const section = (stage: Stage, title: string, items: React.ReactNode[]) =>
    items.length > 0 && (
      <div key={`${stage}${title}`} className="border-t border-line pt-2 first:border-t-0 first:pt-0">
        <button type="button" onClick={() => onPick(stage)} className="label-caps mb-1 text-start text-muted hover:text-text">
          {title}
        </button>
        <ul className="flex flex-col gap-1 text-[12.5px]">{items}</ul>
      </div>
    );
  const line = (key: string, who: string, text: string, tail?: string) => (
    <li key={key} className="leading-snug" dir="auto">
      <span className="font-semibold text-text">{who}</span>
      {tail && <span className="num ms-1.5 text-[11px] text-muted">{tail}</span>} <span className="text-text-soft">{text}</span>
    </li>
  );
  const speeches = (stage: Stage, round: number | null) =>
    turnsOf(room, stage, round).map((x) => {
      const d = x.data as unknown as Reply;
      const who = short(x.seat) + (d.responds_to ? ` → ${short(d.responds_to)}` : "");
      return isAbsent(x.data) ? line(x.seat, who, t("noAnswerShort")) : line(x.seat, who, d.headline || d.text.slice(0, 120), d.lean);
    });

  const debateRounds = [...new Set(turnsOf(room, "debate").map((x) => x.round))];
  const faults = turnsOf(room, "faultlines")[0];

  return (
    <aside className={`${PANEL} flex flex-col gap-2 self-start @3xl:sticky @3xl:top-2.5`} aria-label={t("keyPoints")} data-key-points>
      <h3 className="label-caps text-muted">{t("keyPoints")}</h3>
      {!s || !room.turns.length ? (
        <p className="text-muted">{t("kpEmpty")}</p>
      ) : (
        <div className="flex flex-col gap-2">
          {brief && section("brief", t("kp.brief"), [...brief.focus.map((f, i) => line(`f${i}`, "", f)), ...(brief.note ? [line("note", "", brief.note)] : [])])}
          {section("openings", t("kp.openings", { n: 1 }), speeches("openings", 1))}
          {faults &&
            section(
              "faultlines",
              t("kp.faultlines"),
              (faults.data as unknown as FaultLines).lines.map((f, i) => line(`fl${i}`, f.between.map((x) => short(x)).join(t("versus")), f.title)),
            )}
          {debateRounds.map((r) => section("debate", t("kp.debate", { n: r ?? 2 }), speeches("debate", r)))}
          {section(
            "vote",
            t("kp.vote", { n: s.rounds }),
            turnsOf(room, "vote").map((x) => {
              const d = x.data as unknown as Vote;
              return isAbsent(x.data) ? line(x.seat, short(x.seat), t("noAnswerShort")) : line(x.seat, short(x.seat), d.reason, `${d.top} · ${d.scores[d.top]}`);
            }),
          )}
          {verdict && section("verdict", t("kp.verdict"), [line("v", "", verdict.headline)])}
        </div>
      )}
    </aside>
  );
}
