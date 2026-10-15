"use client";

import { useTranslations } from "next-intl";
import { Panel } from "@/components/panel/Panel";
import type { components } from "@/lib/api/schema";
import { fmtNumber } from "@/lib/format";
import { useTickerCouncil } from "@/lib/queries";
import { useGroupTicker } from "@/lib/ticker-groups";
import { Num, QueryState, toTsv } from "./common";
import { ruleArgs } from "@/lib/council-rules";

type Seat = components["schemas"]["Seat"];
type Vote = Seat["vote"];

const STROKE: Record<Vote, string> = {
  bullish: "stroke-gain",
  neutral: "stroke-neutral-seat",
  bearish: "stroke-loss",
  abstain: "stroke-line",
};

const TEXT: Record<Vote, string> = {
  bullish: "text-gain",
  neutral: "text-text-soft",
  bearish: "text-loss",
  abstain: "text-muted",
};

export function VoteLabel({ vote }: { vote: Vote }) {
  const t = useTranslations("stock.council");
  return (
    <span className={`label-caps flex items-center gap-1.5 ${TEXT[vote]}`}>
      <span
        aria-hidden
        className={`size-2 rounded-full ${
          vote === "abstain" ? "border border-dashed border-muted" : vote === "bullish" ? "bg-gain" : vote === "bearish" ? "bg-loss" : "bg-neutral-seat"
        }`}
      />
      {t(vote)}
    </span>
  );
}

/**
 * Six seats as ring segments, clockwise from the top in seat order. Abstaining
 * seats are drawn in the divider colour. The centre counts bullish seats among
 * the seats that voted: there is no blended score.
 */
export function CouncilRing({
  seats,
  counts,
  size = 148,
}: {
  seats: Seat[];
  counts: Record<string, number>;
  size?: number;
}) {
  const t = useTranslations("stock.council");
  const r = 46;
  const c = 2 * Math.PI * r;
  const gap = 3.2;
  const seg = c / seats.length - gap;
  const voting = seats.length - (counts.abstain ?? 0);

  return (
    <figure className="relative shrink-0" style={{ width: size, height: size }}>
      <svg viewBox="0 0 120 120" width={size} height={size} role="img" aria-label={seats.map((s) => `${t(`seats.${s.seat}`)}: ${t(s.vote)}`).join(", ")}>
        <g transform="rotate(-90 60 60)">
          {seats.map((s, i) => (
            <circle
              key={s.seat}
              cx="60"
              cy="60"
              r={r}
              fill="none"
              className={STROKE[s.vote]}
              strokeWidth={11}
              strokeDasharray={`${seg} ${c - seg}`}
              strokeDashoffset={-(i * (seg + gap))}
            />
          ))}
        </g>
      </svg>
      <figcaption className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="num text-[28px] leading-none text-text">{counts.bullish ?? 0}</span>
        <span className="mt-1 text-[11px] leading-tight text-muted">
          {t("bullishSeats")}
          <br />
          {t("of", { n: voting })}
        </span>
      </figcaption>
    </figure>
  );
}

const INPUT_FORMAT: Record<string, (v: number) => string | null> = {
  pe: (v) => `${fmtNumber(v)}x`,
  roe: (v) => `${fmtNumber(v, 1)}%`,
  dividend_yield: (v) => `${fmtNumber(v, 2)}%`,
  volatility_1y: (v) => `${fmtNumber(v, 1)}%`,
  regime_score: (v) => `${fmtNumber(v, 0)}/100`,
};

function inputValue(name: string, value: number | string | null | undefined): string | null {
  if (value == null) return null;
  if (typeof value === "string") return value;
  return (INPUT_FORMAT[name] ?? ((v: number) => fmtNumber(v, 0)))(value);
}

/** Council tab: each seat with its vote, the database inputs it used, and its rule. */
export function SeatsPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(1);
  const council = useTickerCouncil(slug);
  const c = council.data;

  return (
    <Panel
      id="council.seats"
      title={t("panels.seats")}
      group={1}
      ticker={slug}
      freshness={c ? c.freshness : undefined}
      onRefresh={() => council.refetch()}
      copyData={() =>
        c
          ? toTsv(
              c.seats.flatMap((s) =>
                s.inputs.map((i) => [t(`council.seats.${s.seat}`), t(`council.${s.vote}`), t(`council.inputs.${i.name}`), inputValue(i.name, i.value)]),
              ),
            )
          : null
      }
      copilotData={() => c}
      className={className}
    >
      <QueryState isPending={council.isPending} error={council.error} rows={8}>
        {c && (
          <>
            <p className="mb-3 max-w-[70ch] text-muted">{t("council.method")}</p>
            <ul className="flex flex-col">
              {c.seats.map((s) => (
                <li key={s.seat} className="grid grid-cols-1 gap-2 border-t border-line py-2.5 sm:grid-cols-[110px_minmax(0,1fr)]">
                  <div className="flex items-center justify-between gap-2 sm:flex-col sm:items-start">
                    <span className="headline text-[17px]">{t(`council.seats.${s.seat}`)}</span>
                    <VoteLabel vote={s.vote} />
                  </div>
                  <div className="min-w-0">
                    <dl className="flex flex-wrap gap-x-5 gap-y-1">
                      {s.inputs.map((i) => (
                        <div key={i.name} className="flex items-baseline gap-2">
                          <dt className="text-text-soft">{t(`council.inputs.${i.name}`)}</dt>
                          <dd>
                            <Num value={inputValue(i.name, i.value)} />
                          </dd>
                        </div>
                      ))}
                    </dl>
                    <p className="mt-1 text-[12px] text-muted">
                      <span className="label-caps me-1.5">{t("council.rule")}</span>
                      {t.has(`council.rules.${s.seat}`) ? t(`council.rules.${s.seat}`, ruleArgs(s.thresholds)) : s.rule}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </QueryState>
    </Panel>
  );
}
