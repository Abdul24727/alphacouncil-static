"use client";

import { useLocale, useTranslations } from "next-intl";
import { FreshnessLight, Panel } from "@/components/panel/Panel";
import { LangTag, QueryState, toTsv } from "@/components/stock/common";
import { newsDate } from "@/components/stock/overview-panels";
import type { components } from "@/lib/api/schema";
import { fmtDate, fmtNumber, fmtPct, signClass } from "@/lib/format";
import { newsText } from "@/lib/news-text";
import { useMarketOverview } from "@/lib/queries-app";
import { ChangeCell, PriceCell, TickerCell, TickerRow, Th, useExchangeName } from "./shared";

type Exchange = components["schemas"]["ExchangeSummary"];

/** Advancers / decliners as a two-colour bar with counts. */
export function Breadth({ b }: { b: Exchange["breadth"] }) {
  const total = b.advancers + b.decliners + b.unchanged;
  if (!total) return <span className="label-caps text-muted">—</span>;
  return (
    <div className="flex min-w-28 items-center gap-2">
      <span className="num text-[11px] text-gain">{b.advancers}</span>
      <span className="flex h-1.5 flex-1 overflow-hidden rounded-full bg-line" aria-hidden>
        <span className="bg-gain" style={{ width: `${(b.advancers / total) * 100}%` }} />
        <span className="bg-neutral-seat" style={{ width: `${(b.unchanged / total) * 100}%` }} />
        <span className="bg-loss" style={{ width: `${(b.decliners / total) * 100}%` }} />
      </span>
      <span className="num text-[11px] text-loss">{b.decliners}</span>
    </div>
  );
}

export function ExchangesTable({ rows }: { rows: Exchange[] }) {
  const t = useTranslations("market");
  const locale = useLocale();
  const name = useExchangeName();
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px]">
        <thead>
          <tr>
            <Th>{t("exchange")}</Th>
            <Th end>{t("index")}</Th>
            <Th end>{t("change")}</Th>
            <Th className="ps-4">{t("breadth")}</Th>
            <Th end>{t("equities")}</Th>
            <Th end>{t("asOf")}</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((e) => (
            <tr key={e.exchange} className="border-t border-line" data-exchange={e.exchange}>
              <td className="py-1.5 text-text">{name(e.exchange)}</td>
              <td className="py-1.5 text-end">
                {e.index ? (
                  <span className="inline-flex items-center gap-2">
                    <FreshnessLight freshness={e.index.freshness ?? null} />
                    <span className="num">{fmtNumber(e.index.level)}</span>
                  </span>
                ) : (
                  <span className="label-caps text-muted" title={t("noIndex")}>
                    {t("na")}
                  </span>
                )}
              </td>
              <td className="py-1.5 text-end">
                {e.index ? <span className={`num ${signClass(e.index.change_pct)}`}>{fmtPct(e.index.change_pct, 2, true)}</span> : null}
              </td>
              <td className="py-1.5 ps-4">
                <Breadth b={e.breadth} />
              </td>
              <td className="num py-1.5 text-end text-text-soft">
                {e.with_prices}/{e.equities}
              </td>
              <td className="num py-1.5 text-end text-[11.5px] text-muted">{fmtDate(e.as_of, locale) ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function HomeView() {
  const t = useTranslations("market");
  const locale = useLocale();
  const q = useMarketOverview(locale === "ar" ? "ar" : "en");
  const o = q.data;

  return (
    <div className="@container min-h-0 flex-1 overflow-y-auto">
      <div className="grid grid-cols-12 gap-2.5 p-2.5">
        <Panel
          id="home.markets"
          title={t("markets")}
          onRefresh={() => q.refetch()}
          copyData={() => (o ? toTsv(o.exchanges.map((e) => [e.exchange, e.index?.level, e.index?.change_pct, e.breadth.advancers, e.breadth.decliners, e.as_of])) : null)}
          copilotData={() => o?.exchanges}
          className="col-span-12"
        >
          <QueryState isPending={q.isPending} error={q.error} rows={7}>
            {o && <ExchangesTable rows={o.exchanges} />}
          </QueryState>
        </Panel>

        {(["gainers", "losers"] as const).map((side) => (
          <Panel
            key={side}
            id={`home.${side}`}
            title={t(side)}
            onRefresh={() => q.refetch()}
            copyData={() => (o ? toTsv(o[side].map((m) => [m.ticker.symbol, m.price.close, m.price.change_pct])) : null)}
            copilotData={() => o?.[side]}
            className="col-span-12 @3xl:col-span-6 @6xl:col-span-4"
          >
            <QueryState isPending={q.isPending} error={q.error} empty={!!o && o[side].length === 0} emptyText={t("noMovers")} rows={6}>
              <table className="w-full table-fixed">
                <tbody>
                  {o?.[side].map((m) => (
                    <TickerRow key={m.ticker.ticker_key} ticker={m.ticker}>
                      <td className="py-1.5 pe-2">
                        <TickerCell ticker={m.ticker} />
                      </td>
                      <td className="w-20 py-1.5 text-end">
                        <PriceCell price={m.price} currency={m.ticker.currency} />
                      </td>
                      <td className="w-18 py-1.5 text-end">
                        <ChangeCell value={m.price.change_pct} />
                      </td>
                    </TickerRow>
                  ))}
                </tbody>
              </table>
            </QueryState>
          </Panel>
        ))}

        <Panel
          id="home.news"
          title={t("news")}
          onRefresh={() => q.refetch()}
          copyData={() => (o ? toTsv(o.news.map((n) => [n.date, n.ticker.symbol, n.title, n.url])) : null)}
          copilotData={() => o?.news}
          className="col-span-12 @6xl:col-span-4"
        >
          <QueryState isPending={q.isPending} error={q.error} empty={!!o && o.news.length === 0} emptyText={t("noNews")}>
            <ul className="flex flex-col">
              {o?.news.map((n, i) => {
                // The page's language wherever the database has it (lib/news-text).
                const text = newsText(n, locale);
                return (
                  <li key={i} className="border-t border-line py-2 first:border-t-0 first:pt-0">
                    <div className="mb-0.5 flex items-center gap-2">
                      <span className="num text-[11px] text-muted">{newsDate(n, locale)}</span>
                      <span className="num text-[11px] text-signal">{n.ticker.symbol}</span>
                      {text.foreign && <LangTag lang={text.foreign} />}
                    </div>
                    <a
                      href={n.url ?? undefined}
                      target="_blank"
                      rel="noopener noreferrer"
                      lang={text.lang}
                      dir="auto"
                      className={`text-text hover:text-signal ${text.long ? "line-clamp-3" : ""}`}
                    >
                      {text.title}
                    </a>
                  </li>
                );
              })}
            </ul>
          </QueryState>
        </Panel>
      </div>
    </div>
  );
}
