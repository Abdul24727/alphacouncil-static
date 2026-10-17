"use client";

import { ArrowRightIcon } from "@radix-ui/react-icons";
import { useLocale, useTranslations } from "next-intl";
import { Panel } from "@/components/panel/Panel";
import { dataLabel } from "@/lib/data-labels";
import type { components } from "@/lib/api/schema";
import { currencyLabel, fmtDate, fmtNumber, fmtPct, signClass } from "@/lib/format";
import {
  useTickerCorporate,
  useTickerDetail,
  useTickerEvents,
  useTickerFundamentals,
  useTickerInsights,
  useTickerStatements,
} from "@/lib/queries";
import { useGroupTicker } from "@/lib/ticker-groups";
import { Num, priceDigits, QueryState, toTsv } from "./common";
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
  const locale = useLocale();
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
              <p className="label-caps mb-1.5 text-muted">{t("statements.unit", { currency: currencyLabel(s?.currency, locale) })}</p>
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
                          {/* Labels are stored in one language; shown in the page's when known (lib/data-labels). */}
                          <bdi lang={dataLabel(r.label, locale).lang}>{dataLabel(r.label, locale).text}</bdi>
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

type Ownership = {
  foreign_series?: { date: string; pct: number | null }[] | null;
  foreign_current_pct?: number | null;
  foreign_as_of?: string | null;
  foreign_limit_pct?: number | null;
  major_holders?: { name: string; pct: number | null; as_of?: string | null }[] | null;
  recent_changes?: { date: string | null; name: string; from_pct: number | null; to_pct: number | null; change: number | null }[] | null;
};

export function OwnershipPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(GROUP);
  const q = useTickerInsights(slug);
  const o = (q.data?.ownership ?? null) as Ownership | null;
  const holders = o?.major_holders ?? [];
  const changes = o?.recent_changes ?? [];

  return (
    <Panel
      id="ownership.holders"
      title={t("panels.ownership")}
      group={GROUP}
      ticker={slug}
      onRefresh={() => q.refetch()}
      copyData={() =>
        toTsv([
          [t("ownership.holder"), t("ownership.stake"), t("ownership.asOf")],
          ...holders.map((h) => [h.name, h.pct, h.as_of ?? ""]),
        ])
      }
      copilotData={() => o}
      className={className}
    >
      <QueryState isPending={q.isPending} error={q.error} empty={!o} emptyText={t("ownership.none")}>
        {o && (
          // Sized by the panel's own width (the Copilot and sidebar can take room from it).
          <div className="@container">
            <div className="grid grid-cols-1 gap-x-8 gap-y-5 @3xl:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
              <div className="flex min-w-0 flex-col gap-5">
                <ForeignOwnership o={o} />
                <OwnershipSection title={t("ownership.holders")} empty={holders.length === 0} emptyText={t("ownership.noHolders")}>
                  <HoldersTable holders={holders} />
                </OwnershipSection>
              </div>
              <OwnershipSection title={t("ownership.changes")} empty={changes.length === 0} emptyText={t("ownership.noChanges")}>
                <ChangesTable changes={changes} />
              </OwnershipSection>
            </div>
          </div>
        )}
      </QueryState>
    </Panel>
  );
}

function OwnershipSection({ title, empty, emptyText, children }: { title: string; empty: boolean; emptyText: string; children: React.ReactNode }) {
  return (
    <section aria-label={title} className="min-w-0">
      <h3 className="headline mb-2 border-b border-line pb-1.5 text-[17px]">{title}</h3>
      {empty ? <p className="text-muted">{emptyText}</p> : children}
    </section>
  );
}

function ForeignOwnership({ o }: { o: Ownership }) {
  const t = useTranslations("stock");
  const locale = useLocale();
  const series = (o.foreign_series ?? []).filter((p): p is { date: string; pct: number } => p.pct != null);
  const has = o.foreign_current_pct != null || o.foreign_limit_pct != null || series.length > 0;
  const first = series[0];
  const last = series.at(-1);

  return (
    <OwnershipSection title={t("ownership.foreign")} empty={!has} emptyText={t("ownership.noForeign")}>
      <dl className="flex flex-col gap-1.5">
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-text-soft">{t("ownership.foreignNow")}</dt>
          <dd>
            <Num value={fmtPct(o.foreign_current_pct, 2)} />
          </dd>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <dt className="text-text-soft">{t("ownership.foreignLimit")}</dt>
          <dd>
            <Num value={fmtPct(o.foreign_limit_pct, 2)} />
          </dd>
        </div>
        {o.foreign_as_of && (
          <div className="flex items-baseline justify-between gap-2 text-[11.5px] text-muted">
            <dt>{t("ownership.asOf")}</dt>
            <dd className="num">{fmtDate(o.foreign_as_of, locale)}</dd>
          </div>
        )}
      </dl>
      {first && last && series.length > 1 && (
        <figure className="mt-3" aria-label={t("ownership.trend")}>
          <Sparkline values={series.map((p) => p.pct)} />
          {/* Oldest on the left, like the line; date and value on their own lines so the
              Arabic dates keep their reading order. */}
          <figcaption className="mt-1 flex justify-between gap-2 text-[11px] text-muted" dir="ltr">
            <span className="flex flex-col items-start">
              <span className="num">{fmtDate(first.date, locale)}</span>
              <span className="num text-text-soft">{fmtPct(first.pct, 2)}</span>
            </span>
            <span className="flex flex-col items-end">
              <span className="num">{fmtDate(last.date, locale)}</span>
              <span className="num text-text-soft">{fmtPct(last.pct, 2)}</span>
            </span>
          </figcaption>
        </figure>
      )}
    </OwnershipSection>
  );
}

/** A small line of the stored daily values, oldest on the left in both languages (like the charts). */
function Sparkline({ values }: { values: number[] }) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const points = values
    .map((v, i) => `${(i / (values.length - 1)) * 100},${max === min ? 20 : 36 - ((v - min) / span) * 32}`)
    .join(" ");
  return (
    <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="h-10 w-full text-text-soft" aria-hidden>
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

function HoldersTable({ holders }: { holders: NonNullable<Ownership["major_holders"]> }) {
  const t = useTranslations("stock");
  const locale = useLocale();
  return (
    <table className="w-full">
      <thead>
        <tr className="label-caps text-muted">
          <th className="py-1 text-start font-normal">{t("ownership.holder")}</th>
          <th className="py-1 text-end font-normal">{t("ownership.stake")}</th>
          <th className="hidden py-1 text-end font-normal @sm:table-cell">{t("ownership.asOf")}</th>
        </tr>
      </thead>
      <tbody>
        {holders.map((h, i) => (
          <tr key={i} className="border-t border-line">
            {/* Holder names are stored in one language; known institutions are shown in the page's (lib/data-labels). */}
            <td className="py-1 pe-2 text-text-soft" dir="auto" lang={dataLabel(h.name, locale).lang}>
              {dataLabel(h.name, locale).text}
            </td>
            <td className="py-1 text-end">
              <Num value={fmtPct(h.pct, 2)} />
            </td>
            <td className="num hidden py-1 text-end text-[11.5px] whitespace-nowrap text-muted @sm:table-cell">{fmtDate(h.as_of, locale) ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ChangesTable({ changes }: { changes: NonNullable<Ownership["recent_changes"]> }) {
  const t = useTranslations("stock");
  const locale = useLocale();
  return (
    <table className="w-full">
      <thead>
        <tr className="label-caps text-muted">
          <th className="py-1 text-start font-normal">{t("ownership.date")}</th>
          <th className="py-1 text-start font-normal">{t("ownership.holder")}</th>
          <th className="hidden py-1 text-end font-normal @md:table-cell">{t("ownership.fromTo")}</th>
          <th className="py-1 text-end font-normal">{t("ownership.change")}</th>
        </tr>
      </thead>
      <tbody>
        {changes.map((c, i) => (
          <tr key={i} className="border-t border-line">
            {/* .num makes a cell left-to-right, which would put its end padding on the outer side in Arabic. */}
            <td className="py-1 pe-3 text-[11.5px] whitespace-nowrap">
              <span className="num">{fmtDate(c.date, locale) ?? "—"}</span>
            </td>
            <td className="py-1 pe-3 text-text-soft" dir="auto" lang={dataLabel(c.name, locale).lang}>
              {dataLabel(c.name, locale).text}
            </td>
            <td className="hidden py-1 pe-3 text-end text-[11.5px] whitespace-nowrap text-muted @md:table-cell">
              {/* From -> to in reading order; an icon, since the brand fonts have no arrow glyph. */}
              <span className="inline-flex items-center gap-1">
                <Num value={fmtPct(c.from_pct, 2)} />
                <ArrowRightIcon aria-hidden className="size-3 shrink-0 rtl:-scale-x-100" />
                <Num value={fmtPct(c.to_pct, 2)} />
              </span>
            </td>
            <td className="py-1 text-end">
              <Num value={fmtPct(c.change, 2, true)} className={signClass(c.change)} />
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// --- Calendar: events, dividends, capital changes, seasonality --------------------------------

export function EventsPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const locale = useLocale();
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
      copyData={() => toTsv(items.map((i) => [newsDate(i, locale), i.title]))}
      copilotData={() => items}
      className={className}
    >
      <QueryState isPending={q.isPending} error={q.error} empty={items.length === 0} emptyText={t("events.none")}>
        <ul className="flex flex-col">
          {items.map((i) => (
            <li key={i.id} className="flex items-baseline gap-3 border-t border-line py-1.5 first:border-t-0">
              <span className="num w-24 shrink-0 text-[11.5px] text-muted">{newsDate(i, locale)}</span>
              {i.url ? (
                <a href={i.url} target="_blank" rel="noopener noreferrer" lang={dataLabel(i.title, locale).lang} dir="auto" className="min-w-0 truncate text-text hover:text-signal">
                  {dataLabel(i.title, locale).text}
                </a>
              ) : (
                <span dir="auto" lang={dataLabel(i.title, locale).lang} className="min-w-0 truncate">
                  {dataLabel(i.title, locale).text}
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
  const locale = useLocale();
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
                {t("dividends.dps")} {currencyLabel(c?.currency, locale)}
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
  const locale = useLocale();
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
        <p className="label-caps mb-1.5 text-muted">{t("statements.unit", { currency: currencyLabel(c?.currency, locale) })}</p>
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
                <td className="py-1 text-text-soft" dir="auto" lang={dataLabel(r.change_type, locale).lang}>
                  {dataLabel(r.change_type, locale).text}
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
