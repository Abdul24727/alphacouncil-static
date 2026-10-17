"use client";

import { useLocale, useTranslations } from "next-intl";
import { useSyncExternalStore } from "react";
import { Panel } from "@/components/panel/Panel";
import { TickerNames } from "@/components/ticker/TickerPicker";
import type { NewsItem, TickerDetail } from "@/lib/api/client";
import {
  fmtCompact,
  fmtDate,
  fmtNumber,
  fmtPct,
  fmtRatioPct,
  signClass,
  withCurrency,
} from "@/lib/format";
import { useChartPrefs } from "@/lib/chart-prefs";
import { newsText } from "@/lib/news-text";
import { useTickerCouncil, useTickerDetail, useTickerNews, useTickerPeers, useTickerPrices } from "@/lib/queries";
import { useGroupTicker, useTickerGroups } from "@/lib/ticker-groups";
import { CouncilRing, VoteLabel } from "./council";
import { Num, priceDigits, QueryState, toTsv } from "./common";
import { INDICATORS, PriceChart, RANGES } from "./PriceChart";

const GROUP = 1 as const;

// --- Price ---------------------------------------------------------------------------------

export function PricePanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const locale = useLocale();
  const slug = useGroupTicker(GROUP);
  const prices = useTickerPrices(slug);
  const { mode, range, indicators, setMode, setRange, toggleIndicator } = useChartPrefs();
  const p = prices.data;
  const digits = priceDigits(p?.currency);
  const bars = p?.bars ?? [];

  return (
    <Panel
      id="overview.price"
      title={t("panels.price")}
      group={GROUP}
      ticker={slug}
      freshness={p ? p.freshness : undefined}
      onRefresh={() => prices.refetch()}
      copyData={() =>
        toTsv([["date", "open", "high", "low", "close", "volume"], ...bars.map((b) => [b.time, b.open, b.high, b.low, b.close, b.volume])])
      }
      copilotData={() => ({
        ticker: p?.ticker_key,
        currency: p?.currency,
        range,
        // The Copilot gets the visible window, not ten years of bars.
        bars: bars.slice(-Math.min(bars.length, { "1M": 23, "3M": 66, "6M": 130, "1Y": 260, "5Y": 1300 }[range])),
      })}
      menuItems={INDICATORS.map((i) => ({
        key: i,
        label: t(`chart.indicators.${i}`),
        checked: indicators.includes(i),
        onSelect: () => toggleIndicator(i),
      }))}
      className={className}
      bodyClassName="flex flex-col"
    >
      <QueryState
        isPending={prices.isPending}
        error={prices.error}
        empty={!!p && !p.has_history}
        emptyText={t("price.noHistory")}
      >
        <div className="flex flex-wrap items-center gap-2 border-b border-line px-3 py-1.5">
          <div role="radiogroup" aria-label={t("chart.mode")} className="flex rounded-chip border border-line p-0.5">
            {(["line", "candles"] as const).map((m) => (
              <button
                key={m}
                type="button"
                role="radio"
                aria-checked={mode === m}
                onClick={() => setMode(m)}
                className={`rounded-[3px] px-2 py-0.5 ${mode === m ? "bg-panel-raised text-text" : "text-muted hover:text-text"}`}
              >
                {t(`chart.${m}`)}
              </button>
            ))}
          </div>
          <div role="radiogroup" aria-label={t("chart.range")} className="flex gap-0.5">
            {RANGES.map((r) => (
              <button
                key={r}
                type="button"
                role="radio"
                aria-checked={range === r}
                data-range={r}
                onClick={() => setRange(r)}
                className={`rounded-chip px-1.5 py-0.5 text-[11px] ${locale === "ar" ? "" : "num"} ${range === r ? "text-signal" : "text-muted hover:text-text"}`}
              >
                {t(`chart.ranges.${r}`)}
              </button>
            ))}
          </div>
          {indicators.length > 0 && (
            <span className="label-caps ms-auto truncate text-muted">
              {indicators.map((i) => t(`chart.short.${i}`)).join(" · ")}
            </span>
          )}
        </div>
        <ChartArea bars={bars} mode={mode} range={range} indicators={indicators} digits={digits} />
      </QueryState>
    </Panel>
  );
}

const subscribePhone = (cb: () => void) => {
  const mq = window.matchMedia("(max-width: 767px)");
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
};

/** Taller when RSI / MACD panes are on; shorter on phones. */
function ChartArea(props: Omit<React.ComponentProps<typeof PriceChart>, "height">) {
  const phone = useSyncExternalStore(subscribePhone, () => window.matchMedia("(max-width: 767px)").matches, () => false);
  const panes = (props.indicators.includes("rsi14") ? 1 : 0) + (props.indicators.includes("macd") ? 1 : 0);
  return (
    <div className="px-1 pb-1">
      <PriceChart {...props} height={phone ? 240 + panes * 70 : 340 + panes * 90} />
    </div>
  );
}

// --- Key metrics ---------------------------------------------------------------------------

type MetricRow = [key: string, value: string | null, tone?: number | null];

function metricRows(d: TickerDetail, locale: string): { section: string; rows: MetricRow[] }[] {
  const cur = d.ticker.currency ?? "";
  const q = d.quote;
  const v = d.valuation;
  const r = d.returns;
  const x = d.technicals;
  const mcap = q.market_cap_mn != null ? fmtCompact(q.market_cap_mn * 1e6) : null;
  return [
    {
      section: "trading",
      rows: [
        ["market_cap", withCurrency(mcap, cur, locale)],
        ["volume", fmtCompact(q.volume)],
        ["value_traded", withCurrency(fmtCompact(q.value_traded), cur, locale)],
      ],
    },
    {
      section: "valuation",
      rows: [
        ["pe", v.pe != null ? `${fmtNumber(v.pe)}x` : null],
        ["pb", v.pb != null ? `${fmtNumber(v.pb)}x` : null],
        ["ev_ebitda", v.ev_ebitda != null ? `${fmtNumber(v.ev_ebitda)}x` : null],
        ["dividend_yield", fmtPct(v.dividend_yield_pct)],
        ["roe", fmtPct(v.roe_pct)],
        ["roa", fmtPct(v.roa_pct)],
        ["eps_ttm", v.eps_ttm != null ? `${fmtNumber(v.eps_ttm, priceDigits(cur))} ${cur}` : null],
        ["book_value", v.book_value != null ? `${fmtNumber(v.book_value, priceDigits(cur))} ${cur}` : null],
      ],
    },
    {
      section: "returns",
      rows: [
        ["return_1m", fmtRatioPct(r.return_1m, 1, true), r.return_1m],
        ["return_3m", fmtRatioPct(r.return_3m, 1, true), r.return_3m],
        ["return_6m", fmtRatioPct(r.return_6m, 1, true), r.return_6m],
        ["return_12m", fmtRatioPct(r.return_12m, 1, true), r.return_12m],
        ["vol_1y", fmtRatioPct(r.vol_1y)],
        ["max_drawdown", fmtRatioPct(r.max_drawdown), r.max_drawdown],
        ["rsi_14", fmtNumber(x.rsi_14, 1)],
        ["dist_to_52w_high", fmtPct(x.dist_to_52w_high, 1, true), x.dist_to_52w_high],
      ],
    },
  ];
}

export function MetricsPanel({ className }: { className?: string }) {
  const t = useTranslations("stock.metrics");
  const locale = useLocale();
  const tp = useTranslations("stock.panels");
  const slug = useGroupTicker(GROUP);
  const detail = useTickerDetail(slug);
  const d = detail.data;
  const sections = d ? metricRows(d, locale) : [];
  const fundamentals = d?.freshness.find((f) => f.category === "fundamentals") ?? null;

  return (
    <Panel
      id="overview.metrics"
      title={tp("metrics")}
      group={GROUP}
      ticker={slug}
      freshness={d ? fundamentals : undefined}
      onRefresh={() => detail.refetch()}
      copyData={() => (d ? toTsv(sections.flatMap((s) => s.rows.map(([k, val]) => [t(k), val]))) : null)}
      copilotData={() => d}
      className={className}
      bodyClassName="px-3 pb-3 pt-1"
    >
      <QueryState isPending={detail.isPending} error={detail.error} rows={8}>
        {sections.map((s) => (
          <dl key={s.section} className="mt-2 grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-1">
            <dt className="label-caps col-span-2 mb-0.5 text-muted">{t(s.section)}</dt>
            {s.rows.map(([k, val, tone]) => (
              <div key={k} className="contents">
                <dt className="truncate text-text-soft">{t(k)}</dt>
                <dd className="text-end">
                  <Num value={val} className={tone !== undefined ? signClass(tone) : ""} />
                </dd>
              </div>
            ))}
          </dl>
        ))}
      </QueryState>
    </Panel>
  );
}

// --- Council ring --------------------------------------------------------------------------

export function CouncilPanel({ className, large = false }: { className?: string; large?: boolean }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(GROUP);
  const council = useTickerCouncil(slug);
  const c = council.data;

  return (
    <Panel
      id={large ? "council.ring" : "overview.council"}
      title={t("panels.council")}
      group={GROUP}
      ticker={slug}
      freshness={c ? c.freshness : undefined}
      onRefresh={() => council.refetch()}
      copyData={() =>
        c ? toTsv(c.seats.map((s) => [t(`council.seats.${s.seat}`), t(`council.${s.vote}`)])) : null
      }
      copilotData={() => c}
      className={className}
    >
      <QueryState isPending={council.isPending} error={council.error}>
        {c && (
          <div className={`flex items-center gap-4 ${large ? "flex-col sm:flex-row" : ""}`}>
            <CouncilRing seats={c.seats} counts={c.counts} size={large ? 220 : 148} />
            <ul className="flex w-full min-w-0 flex-1 flex-col gap-1 sm:max-w-72">
              {c.seats.map((s) => (
                <li key={s.seat} className="flex items-center justify-between gap-2">
                  <span className="truncate text-text-soft">{t(`council.seats.${s.seat}`)}</span>
                  <VoteLabel vote={s.vote} />
                </li>
              ))}
            </ul>
          </div>
        )}
      </QueryState>
    </Panel>
  );
}

// --- Peers ---------------------------------------------------------------------------------

export function PeersPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const slug = useGroupTicker(GROUP);
  const setGroupTicker = useTickerGroups((s) => s.setGroupTicker);
  const peers = useTickerPeers(slug);
  const p = peers.data;

  return (
    <Panel
      id="overview.peers"
      title={t("panels.peers")}
      group={GROUP}
      ticker={slug}
      onRefresh={() => peers.refetch()}
      copyData={() =>
        p
          ? toTsv([
              [t("peers.symbol"), t("peers.name"), t("peers.price"), t("peers.change"), t("peers.pe"), t("peers.mcap")],
              ...p.peers.map((r) => [
                r.ticker.symbol,
                r.ticker.name_en ?? r.ticker.name_ar,
                r.last_price,
                r.day_change_pct,
                r.pe,
                r.market_cap_mn,
              ]),
            ])
          : null
      }
      copilotData={() => p}
      className={className}
      bodyClassName="p-0"
    >
      <div className="p-3">
        <QueryState
          isPending={peers.isPending}
          error={peers.error}
          empty={!!p && p.peers.length === 0}
          emptyText={t("peers.none")}
          rows={6}
        >
          {p && (
            <>
              <p className="label-caps mb-1 text-muted">{t(`peers.basis_${p.basis}`)}</p>
              <table className="w-full table-fixed">
                <thead>
                  <tr className="label-caps text-muted">
                    <th className="w-16 py-1 text-start font-normal">{t("peers.symbol")}</th>
                    <th className="py-1 text-start font-normal">{t("peers.name")}</th>
                    <th className="w-20 py-1 text-end font-normal">{t("peers.price")}</th>
                    <th className="w-16 py-1 text-end font-normal">{t("peers.change")}</th>
                  </tr>
                </thead>
                <tbody>
                  {p.peers.map((r) => (
                    <tr
                      key={r.ticker.ticker_key}
                      tabIndex={0}
                      title={t("peers.pick")}
                      data-peer={r.ticker.slug}
                      onClick={() => setGroupTicker(GROUP, r.ticker.slug)}
                      onKeyDown={(e) => e.key === "Enter" && setGroupTicker(GROUP, r.ticker.slug)}
                      className="cursor-pointer border-t border-line hover:bg-panel-raised focus-visible:bg-panel-raised"
                    >
                      <td className="num py-1.5 text-[12px]">{r.ticker.symbol}</td>
                      <td className="py-1.5 pe-2">
                        <TickerNames nameEn={r.ticker.name_en} nameAr={r.ticker.name_ar} single />
                      </td>
                      <td className="py-1.5 text-end">
                        <Num value={fmtNumber(r.last_price, priceDigits(r.ticker.currency))} />
                      </td>
                      <td className="py-1.5 text-end">
                        <Num value={fmtPct(r.day_change_pct, 2, true)} className={signClass(r.day_change_pct)} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </QueryState>
      </div>
    </Panel>
  );
}

// --- News ----------------------------------------------------------------------------------

/** Disclosures and events are stamped 21:00 UTC = midnight in Riyadh of the next day. */
export function newsDate(item: Pick<NewsItem, "date">, locale?: string): string | null {
  if (!item.date) return null;
  if (item.date.length === 10) return fmtDate(item.date, locale);
  const d = new Date(item.date.endsWith("Z") || item.date.includes("+") ? item.date : `${item.date}Z`);
  if (Number.isNaN(d.getTime())) return null;
  const riyadh = new Date(d.getTime() + 3 * 3600_000);
  return fmtDate(riyadh.toISOString().slice(0, 10), locale);
}

export function NewsPanel({ className }: { className?: string }) {
  const t = useTranslations("stock");
  const locale = useLocale();
  const slug = useGroupTicker(GROUP);
  const news = useTickerNews(slug, 10, locale === "ar" ? "ar" : "en");
  const detail = useTickerDetail(slug);
  const freshness = detail.data?.freshness.find((f) => f.category === "news") ?? null;
  const items = news.data ?? [];

  return (
    <Panel
      id="overview.news"
      title={t("panels.news")}
      group={GROUP}
      ticker={slug}
      freshness={detail.data ? freshness : undefined}
      onRefresh={() => news.refetch()}
      copyData={() => toTsv(items.map((i) => [newsDate(i, locale), t(`news.${i.section}`), i.title, i.url]))}
      copilotData={() => items}
      className={className}
    >
      <QueryState isPending={news.isPending} error={news.error} empty={items.length === 0} emptyText={t("news.none")}>
        <ul className="flex flex-col">
          {items.map((i) => {
            // The page's language wherever the database has it (lib/news-text).
            const { title, lang: titleLang, summary, long, foreign } = newsText(i, locale);
            const titleClass = `block text-text ${long ? "line-clamp-3" : ""}`;
            return (
              <li key={i.id} className="border-t border-line py-2 first:border-t-0 first:pt-0">
                <div className="mb-0.5 flex items-center gap-2">
                  <span className="num text-[11px] text-muted">{newsDate(i, locale)}</span>
                  <span className="label-caps rounded-chip border border-line px-1 text-muted">{t(`news.${i.section}`)}</span>
                  {foreign && <span className="label-caps text-muted">{t(`news.in.${foreign}`)}</span>}
                </div>
                {i.url ? (
                  <a
                    href={i.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    lang={titleLang}
                    dir="auto"
                    className={`${titleClass} hover:text-signal`}
                  >
                    {title}
                  </a>
                ) : (
                  <span lang={titleLang} dir="auto" className={titleClass}>
                    {title}
                  </span>
                )}
                {summary && (
                  <p dir="auto" className="mt-0.5 line-clamp-2 text-muted">
                    {summary}
                  </p>
                )}
              </li>
            );
          })}
        </ul>
      </QueryState>
    </Panel>
  );
}
