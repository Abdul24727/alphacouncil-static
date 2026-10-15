"use client";

import { ArrowRightIcon } from "@radix-ui/react-icons";
import Image, { type StaticImageData } from "next/image";
import dividendsAr from "@/assets/screens/dividend-hunter.ar.jpg";
import dividendsEn from "@/assets/screens/dividend-hunter.en.jpg";
import earningsAr from "@/assets/screens/earnings-season.ar.jpg";
import earningsEn from "@/assets/screens/earnings-season.en.jpg";
import sectorsAr from "@/assets/screens/sector-vs-sector.ar.jpg";
import sectorsEn from "@/assets/screens/sector-vs-sector.en.jpg";
import stockAr from "@/assets/screens/tadawul-stock.ar.jpg";
import stockEn from "@/assets/screens/tadawul-stock.en.jpg";
import { useLocale, useTranslations } from "next-intl";
import { useState } from "react";
import { ChangeCell, PriceCell, TickerCell, TickerRow, Th } from "@/components/market/shared";
import { Panel } from "@/components/panel/Panel";
import { Num, priceDigits, QueryState, toTsv } from "@/components/stock/common";
import { Link } from "@/i18n/navigation";
import type { components } from "@/lib/api/schema";
import { fmtCompact, fmtDate, fmtNumber, fmtPct, fmtRatioPct, signClass } from "@/lib/format";
import { useDividendHunter, useEarningsSeason, useSectorCompare, useSectors } from "@/lib/queries-app";
import { TEMPLATES, templateHref, type TemplateName } from "@/lib/templates";

const SCREENS: Record<"en" | "ar", Record<TemplateName, StaticImageData>> = {
  en: { "tadawul-stock": stockEn, "earnings-season": earningsEn, "dividend-hunter": dividendsEn, "sector-vs-sector": sectorsEn },
  ar: { "tadawul-stock": stockAr, "earnings-season": earningsAr, "dividend-hunter": dividendsAr, "sector-vs-sector": sectorsAr },
};

const GRID = "grid grid-cols-12 gap-2.5 p-2.5";

/** Templates list: what each template shows, with a real screen of it (no card grid). */
export function TemplatesList() {
  const t = useTranslations("templates");
  const locale = useLocale() === "ar" ? "ar" : "en";
  return (
    <div className="@container min-h-0 flex-1 overflow-y-auto p-2.5">
      <Panel id="templates.list" title={t("title")} className="col-span-12" bodyClassName="p-0">
        <ul>
          {TEMPLATES.map((name) => (
            <li key={name} className="grid gap-4 border-t border-line p-3 first:border-t-0 @3xl:grid-cols-[minmax(0,1fr)_minmax(0,1.6fr)] @3xl:gap-6">
              <div className="flex flex-col items-start gap-2">
                <Link href={templateHref(name)} className="headline text-[22px] text-text hover:text-signal">
                  {t(`names.${name}`)}
                </Link>
                <p className="max-w-prose text-text-soft">{t(`descriptions.${name}`)}</p>
                <Link href={templateHref(name)} className="label-caps flex items-center gap-1 text-signal hover:underline">
                  {t("open")} <ArrowRightIcon aria-hidden className="rtl:-scale-x-100" />
                </Link>
              </div>
              <Link href={templateHref(name)} className="block overflow-hidden rounded-panel border border-line" tabIndex={-1}>
                <Image
                  src={SCREENS[locale][name]}
                  alt={t("screen", { name: t(`names.${name}`) })}
                  sizes="(min-width: 1200px) 640px, 100vw"
                  className="h-auto w-full"
                />
              </Link>
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}

export function TemplateView({ name }: { name: string }) {
  const t = useTranslations("templates");
  return (
    <div className="@container min-h-0 flex-1 overflow-y-auto">
      {name === "earnings-season" ? (
        <EarningsSeason />
      ) : name === "dividend-hunter" ? (
        <DividendHunter />
      ) : name === "sector-vs-sector" ? (
        <SectorVsSector />
      ) : (
        <p className="p-3 text-muted">{t("unknown")}</p>
      )}
    </div>
  );
}

// --- Earnings Season ---------------------------------------------------------------------------

function EarningsSeason() {
  const t = useTranslations("templates");
  const [days, setDays] = useState(30);
  const q = useEarningsSeason(days);
  const events = q.data?.events ?? [];
  const upcoming = events.filter((e) => e.upcoming);
  const recent = events.filter((e) => !e.upcoming).reverse();

  const table = (rows: typeof events) => (
    <table className="w-full min-w-[520px]">
      <thead>
        <tr>
          <Th>{t("cols.date")}</Th>
          <Th>{t("cols.ticker")}</Th>
          <Th>{t("cols.event")}</Th>
          <Th end>{t("cols.price")}</Th>
          <Th end>{t("cols.change")}</Th>
        </tr>
      </thead>
      <tbody>
        {rows.map((e, i) => (
          <TickerRow key={`${e.ticker.ticker_key}-${e.date}-${i}`} ticker={e.ticker}>
            <td className="num py-1.5 text-[11.5px] text-muted">{fmtDate(e.date)}</td>
            <td className="py-1.5 pe-2">
              <TickerCell ticker={e.ticker} />
            </td>
            <td className="py-1.5 capitalize text-text-soft" dir="auto">{e.title}</td>
            <td className="py-1.5 text-end">
              <PriceCell price={e.price} currency={e.ticker.currency} />
            </td>
            <td className="py-1.5 text-end">
              <ChangeCell value={e.price.change_pct} />
            </td>
          </TickerRow>
        ))}
      </tbody>
    </table>
  );

  return (
    <div className={GRID}>
      <div className="col-span-12 flex items-center gap-2">
        <span className="label-caps text-muted">{t("window")}</span>
        {[14, 30, 60].map((d) => (
          <button key={d} type="button" aria-pressed={days === d} onClick={() => setDays(d)} className={`num rounded-chip px-2 py-0.5 text-[11.5px] ${days === d ? "text-signal" : "text-muted hover:text-text"}`}>
            ±{d}d
          </button>
        ))}
      </div>
      {(["upcoming", "recent"] as const).map((k) => (
        <Panel
          key={k}
          id={`earnings.${k}`}
          title={t(`earnings.${k}`)}
          onRefresh={() => q.refetch()}
          copyData={() => toTsv((k === "upcoming" ? upcoming : recent).map((e) => [e.date, e.ticker.symbol, e.title]))}
          copilotData={() => (k === "upcoming" ? upcoming : recent)}
          className="col-span-12 @5xl:col-span-6"
        >
          <div className="overflow-x-auto">
            <QueryState isPending={q.isPending} error={q.error} empty={!!q.data && (k === "upcoming" ? upcoming : recent).length === 0} emptyText={t("earnings.none")}>
              {table(k === "upcoming" ? upcoming : recent)}
            </QueryState>
          </div>
        </Panel>
      ))}
    </div>
  );
}

// --- Dividend Hunter --------------------------------------------------------------------------

function DividendHunter() {
  const t = useTranslations("templates");
  const [minYield, setMinYield] = useState(3);
  const q = useDividendHunter(minYield);
  const rows = q.data ?? [];

  return (
    <div className={GRID}>
      <Panel
        id="dividends.ranked"
        title={t("dividends.title")}
        onRefresh={() => q.refetch()}
        copyData={() => toTsv(rows.map((r) => [r.ticker.symbol, r.dividend_yield_pct, r.payments_3y, r.last_dps, r.last_ex_date, r.next_ex_date, r.payout_pct]))}
        copilotData={() => rows.slice(0, 40)}
        className="col-span-12"
        bodyClassName="p-0"
      >
        <div className="flex items-center gap-2 border-b border-line p-2">
          <span className="label-caps text-muted">{t("dividends.minYield")}</span>
          {[0, 3, 5, 7].map((y) => (
            <button key={y} type="button" aria-pressed={minYield === y} onClick={() => setMinYield(y)} className={`num rounded-chip px-2 py-0.5 text-[11.5px] ${minYield === y ? "text-signal" : "text-muted hover:text-text"}`}>
              {y}%
            </button>
          ))}
          <span className="num ms-auto text-[12px] text-muted">{rows.length}</span>
        </div>
        <div className="overflow-x-auto p-2">
          <QueryState isPending={q.isPending} error={q.error} rows={10} empty={!!q.data && rows.length === 0} emptyText={t("dividends.none")}>
            <table className="w-full min-w-[820px]">
              <thead>
                <tr>
                  <Th>{t("cols.ticker")}</Th>
                  <Th end>{t("cols.price")}</Th>
                  <Th end>{t("dividends.yield")}</Th>
                  <Th end>{t("dividends.payments")}</Th>
                  <Th end>{t("dividends.lastDps")}</Th>
                  <Th end>{t("dividends.lastEx")}</Th>
                  <Th end>{t("dividends.nextEx")}</Th>
                  <Th end>{t("dividends.payout")}</Th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <TickerRow key={r.ticker.ticker_key} ticker={r.ticker}>
                    <td className="py-1.5 pe-2">
                      <TickerCell ticker={r.ticker} />
                    </td>
                    <td className="py-1.5 text-end">
                      <PriceCell price={r.price} currency={r.ticker.currency} />
                    </td>
                    <td className="num py-1.5 text-end text-text">{fmtPct(r.dividend_yield_pct, 2)}</td>
                    <td className="num py-1.5 text-end">{r.payments_3y}</td>
                    <td className="py-1.5 text-end">
                      <Num value={fmtNumber(r.last_dps, priceDigits(r.ticker.currency) + 1)} />
                    </td>
                    <td className="num py-1.5 text-end text-[11.5px] text-muted">{r.last_ex_date ?? "—"}</td>
                    <td className="num py-1.5 text-end text-[11.5px] text-signal">{r.next_ex_date ?? ""}</td>
                    <td className="py-1.5 text-end">
                      <Num value={fmtPct(r.payout_pct, 0)} />
                    </td>
                  </TickerRow>
                ))}
              </tbody>
            </table>
          </QueryState>
        </div>
      </Panel>
    </div>
  );
}

// --- Sector vs Sector -------------------------------------------------------------------------

type Stats = components["schemas"]["SectorStats"];

function SectorVsSector() {
  const t = useTranslations("templates");
  const locale = useLocale();
  const sectors = useSectors();
  const list = sectors.data ?? [];
  const [a, setA] = useState<string | null>(null);
  const [b, setB] = useState<string | null>(null);
  const sa = a ?? list[0]?.sector_en ?? null;
  const sb = b ?? list[1]?.sector_en ?? null;
  const q = useSectorCompare(sa, sb);
  const c = q.data;
  const label = (s: { sector_en: string; sector_ar?: string | null }) => (locale === "ar" ? (s.sector_ar ?? s.sector_en) : s.sector_en);
  const select = "h-8 rounded-panel border border-line bg-bg px-2 text-text outline-none";

  const statRows: [string, (s: Stats) => string | null][] = [
    ["equities", (s) => String(s.equities)],
    ["medianPe", (s) => (s.median_pe != null ? `${fmtNumber(s.median_pe, 1)}x` : null)],
    ["medianPb", (s) => (s.median_pb != null ? `${fmtNumber(s.median_pb, 2)}x` : null)],
    ["medianYield", (s) => fmtPct(s.median_yield_pct, 2)],
    ["medianRoe", (s) => fmtPct(s.median_roe_pct, 1)],
    ["medianR12", (s) => fmtRatioPct(s.median_return_12m, 1, true)],
  ];

  return (
    <div className={GRID}>
      <div className="col-span-12 flex flex-wrap items-center gap-2">
        <select className={select} value={sa ?? ""} onChange={(e) => setA(e.target.value)} aria-label={t("sectors.a")}>
          {list.map((s) => (
            <option key={s.sector_en} value={s.sector_en}>
              {label(s)} ({s.equities})
            </option>
          ))}
        </select>
        <span className="label-caps text-muted">vs</span>
        <select className={select} value={sb ?? ""} onChange={(e) => setB(e.target.value)} aria-label={t("sectors.b")}>
          {list.map((s) => (
            <option key={s.sector_en} value={s.sector_en}>
              {label(s)} ({s.equities})
            </option>
          ))}
        </select>
      </div>

      <Panel
        id="sectors.compare"
        title={t("sectors.compare")}
        onRefresh={() => q.refetch()}
        copyData={() => (c ? toTsv([["", c.a.sector_en, c.b.sector_en], ...statRows.map(([k, f]) => [k, f(c.a), f(c.b)])]) : null)}
        copilotData={() => (c ? { a: c.a, b: c.b } : null)}
        className="col-span-12"
      >
        <QueryState isPending={sectors.isPending || q.isPending} error={sectors.error ?? q.error} rows={6}>
          {c && (
            <>
              <table className="w-full">
                <thead>
                  <tr>
                    <Th />
                    <Th end>{label(c.a)}</Th>
                    <Th end>{label(c.b)}</Th>
                  </tr>
                </thead>
                <tbody>
                  {statRows.map(([k, f]) => (
                    <tr key={k} className="border-t border-line">
                      <td className="py-1.5 text-text-soft">{t(`sectors.${k}`)}</td>
                      <td className="py-1.5 text-end"><Num value={f(c.a)} /></td>
                      <td className="py-1.5 text-end"><Num value={f(c.b)} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-2 text-[12px] text-muted">{t("sectors.note")}</p>
            </>
          )}
        </QueryState>
      </Panel>

      {c &&
        ([
          ["a", c.a, c.a_members],
          ["b", c.b, c.b_members],
        ] as const).map(([k, s, members]) => (
          <Panel
            key={k}
            id={`sectors.members.${k}`}
            title={label(s)}
            copyData={() => toTsv(members.map((m) => [m.ticker.symbol, m.price.close, m.market_cap_mn, m.pe, m.dividend_yield_pct, m.return_12m]))}
            copilotData={() => members}
            className="col-span-12 @5xl:col-span-6"
          >
            <div className="max-h-[460px] overflow-auto">
              <table className="w-full min-w-[480px]">
                <thead className="sticky top-0 bg-panel">
                  <tr>
                    <Th>{t("cols.ticker")}</Th>
                    <Th end>{t("cols.price")}</Th>
                    <Th end>{t("sectors.mcap")}</Th>
                    <Th end>P/E</Th>
                    <Th end>{t("dividends.yield")}</Th>
                    <Th end>12M</Th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((m) => (
                    <TickerRow key={m.ticker.ticker_key} ticker={m.ticker}>
                      <td className="py-1.5 pe-2"><TickerCell ticker={m.ticker} /></td>
                      <td className="py-1.5 text-end"><PriceCell price={m.price} currency={m.ticker.currency} /></td>
                      <td className="py-1.5 text-end"><Num value={m.market_cap_mn != null ? `${fmtCompact(m.market_cap_mn * 1e6)} ${m.ticker.currency ?? ""}` : null} /></td>
                      <td className="py-1.5 text-end"><Num value={m.pe != null ? fmtNumber(m.pe, 1) : null} /></td>
                      <td className="py-1.5 text-end"><Num value={fmtPct(m.dividend_yield_pct, 2)} /></td>
                      <td className="py-1.5 text-end"><Num value={fmtRatioPct(m.return_12m, 1, true)} className={signClass(m.return_12m)} /></td>
                    </TickerRow>
                  ))}
                </tbody>
              </table>
            </div>
          </Panel>
        ))}
    </div>
  );
}
