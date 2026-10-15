"use client";

import { useTranslations } from "next-intl";
import { Panel } from "@/components/panel/Panel";
import type { components } from "@/lib/api/schema";
import { fmtNumber, fmtPct } from "@/lib/format";
import {
  useTickerCorporate,
  useTickerDetail,
  useTickerEvents,
  useTickerFundamentals,
  useTickerInsights,
  useTickerStatements,
} from "@/lib/queries";
import { useGroupTicker } from "@/lib/ticker-groups";
import { hasArabic, Num, priceDigits, QueryState, toTsv } from "./common";
import { newsDate } from "./overview-panels";

const GROUP = 1 as const;
type GaugeMetric = components["schemas"]["GaugeMetric"];

// --- Fundamentals: four groups, sector percentiles ------------------------------------------

function metricValue(m: GaugeMetric): string | null {
  if (m.value == null) return null;
  if (m.unit === "%") return fmtPct(m.value, 1);
  if (m.unit === "x") return `${fmtNumber(m.value, 1)}x`;
  return fmtNumber(m.value, 2);
}

function PercentileBar({ value }: { value: number | null | undefined }) {
  if (value == null) return <span className="h-1 w-full rounded-full bg-line" />;
  const tone = value >= 67 ? "bg-gain" : value >= 40 ? "bg-neutral-seat" : "bg-loss";
  return (
    <span className="relative h-1 w-full overflow-hidden rounded-full bg-line">
      <span className={`absolute inset-y-0 start-0 ${tone}`} style={{ width: `${Math.max(2, value)}%` }} />
    </span>
  );
}

export function FundamentalsPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(GROUP);
  const q = useTickerFundamentals(slug);
  const f = q.data;

  return (
    <Panel
      id="financials.fundamentals"
      title={t("panels.fundamentals")}
      group={GROUP}
      ticker={slug}
      freshness={f ? f.freshness : undefined}
      onRefresh={() => q.refetch()}
      copyData={() =>
        f
          ? toTsv(
              f.groups.flatMap((g) =>
                g.metrics.map((m) => [t(`fundamentals.${g.group}`), t(`fundamentals.keys.${m.key}`), m.value, m.sector_percentile, m.status]),
              ),
            )
          : null
      }
      copilotData={() => f}
      className={className}
    >
      <QueryState isPending={q.isPending} error={q.error} rows={6}>
        {f && (
          <div className="grid grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-2 xl:grid-cols-4">
            {f.groups.map((g) => (
              <section key={g.group} aria-label={t(`fundamentals.${g.group}`)}>
                <header className="mb-2 flex items-baseline justify-between gap-2 border-b border-line pb-1.5">
                  <h3 className="headline text-[17px]">{t(`fundamentals.${g.group}`)}</h3>
                  {g.score != null ? (
                    <span className="num text-[12px] text-text-soft" title={t("fundamentals.percentile")}>
                      P{fmtNumber(g.score, 0)}
                    </span>
                  ) : (
                    <span className="label-caps text-muted">{t("fundamentals.noScore")}</span>
                  )}
                </header>
                <ul className="flex flex-col gap-1.5">
                  {g.metrics.map((m) => (
                    <li key={m.key} title={t(`fundamentals.status.${m.status}`)}>
                      <div className="flex items-baseline justify-between gap-2">
                        <span className="truncate text-text-soft">{t(`fundamentals.keys.${m.key}`)}</span>
                        <Num value={metricValue(m)} />
                      </div>
                      <div className="mt-1 flex items-center gap-2">
                        <PercentileBar value={m.sector_percentile} />
                        <span className="num w-8 shrink-0 text-end text-[10.5px] text-muted">
                          {m.sector_percentile != null ? `P${fmtNumber(m.sector_percentile, 0)}` : ""}
                        </span>
                      </div>
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>
        )}
      </QueryState>
    </Panel>
  );
}

// --- Statements -----------------------------------------------------------------------------

function statementValue(v: number | null | undefined) {
  if (v == null) return null;
  return fmtNumber(v, Math.abs(v) >= 100 ? 0 : 2);
}

export function StatementPanel({ section, className }: { section: "Income Statement" | "Balance Sheet"; className?: string }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(GROUP);
  const q = useTickerStatements(slug);
  const s = q.data;
  const statement = s?.statements.find((x) => x.section === section);
  const years = s?.years ?? [];
  const id = section === "Income Statement" ? "income" : "balance";

  return (
    <Panel
      id={`financials.${id}`}
      title={t(`panels.${id}`)}
      group={GROUP}
      ticker={slug}
      onRefresh={() => q.refetch()}
      copyData={() =>
        statement ? toTsv([[t("statements.item"), ...years], ...statement.rows.map((r) => [r.label, ...years.map((y) => r.values[String(y)])])]) : null
      }
      copilotData={() => (statement ? { section, unit: s?.unit, currency: s?.currency, years, rows: statement.rows } : null)}
      className={className}
      bodyClassName="p-0"
    >
      <div className="p-3">
        <QueryState isPending={q.isPending} error={q.error} empty={!!s && !statement} emptyText={t("statements.none")} rows={10}>
          {statement && (
            <>
              <p className="label-caps mb-1.5 text-muted">{t("statements.unit", { currency: s?.currency ?? "" })}</p>
              <div className="max-h-[560px] overflow-auto">
                <table className="w-full min-w-[560px]">
                  <thead className="sticky top-0 bg-panel">
                    <tr className="label-caps text-muted">
                      <th className="py-1 text-start font-normal">{t("statements.item")}</th>
                      {years.map((y) => (
                        <th key={y} className="num w-20 py-1 text-end font-normal">
                          FY{y}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {statement.rows.map((r) => (
                      <tr key={r.index} className="border-t border-line">
                        <td className="min-w-48 py-1 pe-3 text-start text-text-soft">
                          {/* Labels are stored as published (often Arabic); bdi keeps their direction without breaking the column's alignment. */}
                          <bdi lang={hasArabic(r.label) ? "ar" : "en"}>{r.label}</bdi>
                        </td>
                        {years.map((y) => (
                          <td key={y} className="py-1 text-end">
                            {r.values[String(y)] == null ? (
                              <span className="text-line">·</span>
                            ) : (
                              <span className={`num ${(r.values[String(y)] ?? 0) < 0 ? "text-loss" : ""}`}>
                                {statementValue(r.values[String(y)])}
                              </span>
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </QueryState>
      </div>
    </Panel>
  );
}

// --- Ownership ------------------------------------------------------------------------------

export function OwnershipPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(GROUP);
  const q = useTickerInsights(slug);
  const ownership = q.data?.ownership;

  return (
    <Panel
      id="ownership.holders"
      title={t("panels.ownership")}
      group={GROUP}
      ticker={slug}
      onRefresh={() => q.refetch()}
      copilotData={() => ownership ?? null}
      className={className}
    >
      <QueryState isPending={q.isPending} error={q.error} empty={!ownership} emptyText={t("ownership.none")}>
        <pre className="num overflow-auto text-[11px] text-text-soft">{JSON.stringify(ownership, null, 2)}</pre>
      </QueryState>
    </Panel>
  );
}

// --- Calendar: events, dividends, capital changes, seasonality --------------------------------

export function EventsPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(GROUP);
  const q = useTickerEvents(slug, 20);
  const items = q.data ?? [];

  return (
    <Panel
      id="calendar.events"
      title={t("panels.events")}
      group={GROUP}
      ticker={slug}
      onRefresh={() => q.refetch()}
      copyData={() => toTsv(items.map((i) => [newsDate(i), i.title]))}
      copilotData={() => items}
      className={className}
    >
      <QueryState isPending={q.isPending} error={q.error} empty={items.length === 0} emptyText={t("events.none")}>
        <ul className="flex flex-col">
          {items.map((i) => (
            <li key={i.id} className="flex items-baseline gap-3 border-t border-line py-1.5 first:border-t-0">
              <span className="num w-24 shrink-0 text-[11.5px] text-muted">{newsDate(i)}</span>
              {i.url ? (
                <a href={i.url} target="_blank" rel="noopener noreferrer" lang={i.lang ?? undefined} dir="auto" className="min-w-0 truncate capitalize text-text hover:text-signal">
                  {i.title}
                </a>
              ) : (
                <span dir="auto" className="min-w-0 truncate capitalize">
                  {i.title}
                </span>
              )}
            </li>
          ))}
        </ul>
      </QueryState>
    </Panel>
  );
}

export function DividendsPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(GROUP);
  const q = useTickerCorporate(slug);
  const c = q.data;
  const rows = c?.dividends ?? [];
  const digits = priceDigits(c?.currency) + 1;

  return (
    <Panel
      id="calendar.dividends"
      title={t("panels.dividends")}
      group={GROUP}
      ticker={slug}
      onRefresh={() => q.refetch()}
      copyData={() =>
        toTsv([[t("dividends.period"), t("dividends.ex_date"), t("dividends.pay_date"), t("dividends.dps")], ...rows.map((d) => [d.note, d.ex_date, d.pay_date, d.dps])])
      }
      copilotData={() => c}
      className={className}
    >
      <QueryState isPending={q.isPending} error={q.error} empty={!!c && rows.length === 0} emptyText={t("dividends.none")}>
        <table className="w-full">
          <thead>
            <tr className="label-caps text-muted">
              <th className="py-1 text-start font-normal">{t("dividends.period")}</th>
              <th className="py-1 text-start font-normal">{t("dividends.ex_date")}</th>
              <th className="hidden py-1 text-start font-normal sm:table-cell">{t("dividends.pay_date")}</th>
              <th className="py-1 text-end font-normal">
                {t("dividends.dps")} {c?.currency}
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((d, i) => (
              <tr key={i} className="border-t border-line">
                <td className="num py-1 text-[11.5px] text-text-soft">{d.note?.replace(/\s*_\s*/, " ")}</td>
                <td className="num py-1 text-[11.5px]">{d.ex_date ?? "—"}</td>
                <td className="num hidden py-1 text-[11.5px] text-muted sm:table-cell">{d.pay_date ?? "—"}</td>
                <td className="py-1 text-end">
                  <Num value={fmtNumber(d.dps, digits)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </QueryState>
    </Panel>
  );
}

export function CapitalPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(GROUP);
  const q = useTickerCorporate(slug);
  const c = q.data;
  const rows = c?.capital_changes ?? [];

  return (
    <Panel
      id="calendar.capital"
      title={t("panels.capital")}
      group={GROUP}
      ticker={slug}
      onRefresh={() => q.refetch()}
      copyData={() => toTsv(rows.map((r) => [r.date, r.change_type, r.capital_before_mn, r.capital_after_mn, r.change_pct]))}
      copilotData={() => rows}
      className={className}
    >
      <QueryState isPending={q.isPending} error={q.error} empty={!!c && rows.length === 0} emptyText={t("capital.none")}>
        <p className="label-caps mb-1.5 text-muted">{t("statements.unit", { currency: c?.currency ?? "" })}</p>
        <table className="w-full">
          <thead>
            <tr className="label-caps text-muted">
              <th className="py-1 text-start font-normal">{t("capital.date")}</th>
              <th className="py-1 text-start font-normal">{t("capital.type")}</th>
              <th className="py-1 text-end font-normal">{t("capital.after")}</th>
              <th className="py-1 text-end font-normal">{t("capital.change")}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} className="border-t border-line" title={r.note ?? undefined}>
                <td className="num py-1 text-[11.5px]">{r.date}</td>
                <td className="py-1 text-text-soft" dir="auto">
                  {r.change_type}
                </td>
                <td className="py-1 text-end">
                  <Num value={fmtNumber(r.capital_after_mn, 0)} />
                </td>
                <td className="py-1 text-end">
                  <Num value={fmtPct(r.change_pct, 1, true)} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </QueryState>
    </Panel>
  );
}

function heat(v: number | null | undefined): React.CSSProperties | undefined {
  if (v == null) return undefined;
  const strength = Math.min(1, Math.abs(v) / 25);
  const pct = Math.round(12 + strength * 48);
  const color = v >= 0 ? "var(--color-gain)" : "var(--color-loss)";
  return { backgroundColor: `color-mix(in srgb, ${color} ${pct}%, transparent)` };
}

export function SeasonalityPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(GROUP);
  const q = useTickerInsights(slug);
  const s = q.data?.seasonality as
    | { years: { year: number; monthly_pct: (number | null)[]; partial: boolean }[]; average: (number | null)[] }
    | null
    | undefined;
  const detail = useTickerDetail(slug);
  const prices = detail.data?.freshness.find((f) => f.category === "prices") ?? null;
  const months = Array.from({ length: 12 }, (_, i) => t(`seasonality.months.${i + 1}`));

  return (
    <Panel
      id="calendar.seasonality"
      title={t("panels.seasonality")}
      group={GROUP}
      ticker={slug}
      freshness={detail.data ? prices : undefined}
      onRefresh={() => q.refetch()}
      copyData={() => (s ? toTsv([["", ...months], ...s.years.map((y) => [y.year, ...y.monthly_pct])]) : null)}
      copilotData={() => s}
      className={className}
    >
      <QueryState isPending={q.isPending} error={q.error} empty={!s || s.years.length === 0} emptyText={t("seasonality.none")}>
        {s && (
          <div className="overflow-x-auto">
            <p className="mb-2 text-muted">{t("seasonality.note")}</p>
            <table className="w-full min-w-[560px] border-separate border-spacing-0.5">
              <thead>
                <tr className="label-caps text-muted">
                  <th className="w-12" />
                  {months.map((m) => (
                    <th key={m} className="py-0.5 text-center font-normal">
                      {m}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {s.years.map((y) => (
                  <tr key={y.year}>
                    <th className="num pe-1 text-start text-[11px] font-normal text-muted">{y.year}</th>
                    {y.monthly_pct.map((v, i) => (
                      <td key={i} className="num rounded-[2px] py-1 text-center text-[10.5px]" style={heat(v)}>
                        {v == null ? "" : fmtNumber(v, 1)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </QueryState>
    </Panel>
  );
}
