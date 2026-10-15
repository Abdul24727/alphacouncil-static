"use client";

import { createColumnHelper, createSortedRowModel, rowSortingFeature, sortFns, tableFeatures, useTable } from "@tanstack/react-table";
import { useLocale, useTranslations } from "next-intl";
import { useMemo, useState } from "react";
import { Panel } from "@/components/panel/Panel";
import { Num, QueryState, toTsv } from "@/components/stock/common";
import type { components } from "@/lib/api/schema";
import { fmtCompact, fmtNumber, fmtPct, fmtRatioPct, signClass } from "@/lib/format";
import { useScreener } from "@/lib/queries-app";
import { normalizeSearch } from "@/lib/search-text";
import { ChangeCell, PriceCell, TickerCell, useExchangeName, useOpenTicker } from "./shared";

type Row = components["schemas"]["ScreenerRow"];

// TanStack Table v9: features and the column helper live at module scope (stable inputs).
const features = tableFeatures({ rowSortingFeature, sortedRowModel: createSortedRowModel(), sortFns });
const col = createColumnHelper<typeof features, Row>();

type Filters = {
  text: string;
  exchanges: string[];
  sector: string;
  peMax: string;
  yieldMin: string;
  roeMin: string;
  r12Min: string;
  mcapMin: string;
};

const EMPTY: Filters = { text: "", exchanges: [], sector: "", peMax: "", yieldMin: "", roeMin: "", r12Min: "", mcapMin: "" };
const EXCHANGES = ["TADAWUL", "ADX", "DFM", "QSE", "KSE", "BSE", "MSM"];

const num = (s: string) => (s.trim() === "" || Number.isNaN(Number(s)) ? null : Number(s));

function matches(r: Row, f: Filters): boolean {
  const t = r.ticker;
  if (f.exchanges.length && !f.exchanges.includes(t.exchange)) return false;
  if (f.sector && t.sector_en !== f.sector) return false;
  if (f.text) {
    const q = normalizeSearch(f.text);
    const hay = normalizeSearch(`${t.symbol} ${t.name_en ?? ""} ${t.name_ar ?? ""}`);
    if (!hay.includes(q)) return false;
  }
  const peMax = num(f.peMax);
  if (peMax != null && !(r.pe != null && r.pe > 0 && r.pe <= peMax)) return false;
  const yMin = num(f.yieldMin);
  if (yMin != null && !(r.dividend_yield_pct != null && r.dividend_yield_pct >= yMin)) return false;
  const roeMin = num(f.roeMin);
  if (roeMin != null && !(r.roe_pct != null && r.roe_pct >= roeMin)) return false;
  const r12 = num(f.r12Min);
  if (r12 != null && !(r.return_12m != null && r.return_12m * 100 >= r12)) return false;
  const mcap = num(f.mcapMin);
  if (mcap != null && !(r.market_cap_mn != null && r.market_cap_mn >= mcap)) return false;
  return true;
}

/** `initialExchange` comes from ?exchange= (the Markets page links here per exchange). */
export function ScreenerView({ initialExchange }: { initialExchange?: string }) {
  const t = useTranslations("screener");
  const locale = useLocale();
  const exName = useExchangeName();
  const open = useOpenTicker();
  const q = useScreener();
  const [f, setF] = useState<Filters>(() =>
    initialExchange && EXCHANGES.includes(initialExchange) ? { ...EMPTY, exchanges: [initialExchange] } : EMPTY,
  );

  const rows = useMemo(() => (q.data ?? []).filter((r) => matches(r, f)), [q.data, f]);
  const sectors = useMemo(() => {
    const m = new Map<string, string | null>();
    for (const r of q.data ?? []) if (r.ticker.sector_en) m.set(r.ticker.sector_en, r.ticker.sector_ar ?? null);
    return [...m].sort((a, b) => a[0].localeCompare(b[0]));
  }, [q.data]);

  const columns = useMemo(
    () =>
      col.columns([
        col.accessor((r) => r.ticker.symbol, { id: "ticker", header: t("cols.ticker"), cell: (c) => <TickerCell ticker={c.row.original.ticker} /> }),
        col.accessor((r) => r.ticker.exchange, { id: "exchange", header: t("cols.exchange"), cell: (c) => <span className="label-caps text-muted">{exName(c.getValue())}</span> }),
        col.accessor((r) => (locale === "ar" ? r.ticker.sector_ar : r.ticker.sector_en) ?? "", { id: "sector", header: t("cols.sector"), cell: (c) => <span className="truncate text-text-soft">{c.getValue()}</span> }),
        col.accessor((r) => r.price.close ?? undefined, { id: "price", header: t("cols.price"), sortUndefined: "last", meta: { end: true }, cell: (c) => <PriceCell price={c.row.original.price} currency={c.row.original.ticker.currency} /> }),
        col.accessor((r) => r.price.change_pct ?? undefined, { id: "change", header: t("cols.change"), sortUndefined: "last", meta: { end: true }, cell: (c) => <ChangeCell value={c.getValue()} /> }),
        col.accessor((r) => r.market_cap_mn ?? undefined, { id: "mcap", header: t("cols.mcap"), sortUndefined: "last", meta: { end: true }, cell: (c) => <Num value={c.getValue() != null ? fmtCompact(c.getValue()! * 1e6) : null} /> }),
        col.accessor((r) => r.pe ?? undefined, { id: "pe", header: t("cols.pe"), sortUndefined: "last", meta: { end: true }, cell: (c) => <Num value={c.getValue() != null ? `${fmtNumber(c.getValue(), 1)}x` : null} /> }),
        col.accessor((r) => r.dividend_yield_pct ?? undefined, { id: "yield", header: t("cols.yield"), sortUndefined: "last", meta: { end: true }, cell: (c) => <Num value={fmtPct(c.getValue(), 2)} /> }),
        col.accessor((r) => r.roe_pct ?? undefined, { id: "roe", header: t("cols.roe"), sortUndefined: "last", meta: { end: true }, cell: (c) => <Num value={fmtPct(c.getValue(), 1)} /> }),
        col.accessor((r) => r.return_12m ?? undefined, { id: "r12", header: t("cols.r12"), sortUndefined: "last", meta: { end: true }, cell: (c) => <Num value={fmtRatioPct(c.getValue(), 1, true)} className={signClass(c.getValue())} /> }),
        col.accessor((r) => r.rsi_14 ?? undefined, { id: "rsi", header: t("cols.rsi"), sortUndefined: "last", meta: { end: true }, cell: (c) => <Num value={fmtNumber(c.getValue(), 0)} /> }),
      ]),
    [t, exName, locale],
  );

  const table = useTable({ features, columns, data: rows });

  const input = "h-8 rounded-panel border border-line bg-bg px-2 text-text outline-none focus:border-muted";
  const numInput = `${input} num w-20 text-[12px]`;
  const set = (k: keyof Filters) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value });

  return (
    <div className="flex min-h-0 flex-1 flex-col p-2.5">
      <Panel
        id="screener.results"
        title={t("title")}
        onRefresh={() => q.refetch()}
        copyData={() =>
          toTsv([
            ["symbol", "exchange", "sector", "close", "change_pct", "market_cap_mn", "pe", "yield_pct", "roe_pct", "return_12m", "rsi_14"],
            ...rows.map((r) => [r.ticker.symbol, r.ticker.exchange, r.ticker.sector_en, r.price.close, r.price.change_pct, r.market_cap_mn, r.pe, r.dividend_yield_pct, r.roe_pct, r.return_12m, r.rsi_14]),
          ])
        }
        copilotData={() => ({ filters: f, matches: rows.length, top: rows.slice(0, 40) })}
        className="min-h-0 flex-1"
        bodyClassName="flex min-h-0 flex-col"
      >
        <div className="flex flex-wrap items-end gap-2 border-b border-line p-2">
          <input className={`${input} w-48`} placeholder={t("search")} value={f.text} onChange={set("text")} aria-label={t("search")} />
          <div className="flex flex-wrap gap-1" role="group" aria-label={t("cols.exchange")}>
            {EXCHANGES.map((ex) => {
              const on = f.exchanges.includes(ex);
              return (
                <button
                  key={ex}
                  type="button"
                  aria-pressed={on}
                  onClick={() => setF({ ...f, exchanges: on ? f.exchanges.filter((x) => x !== ex) : [...f.exchanges, ex] })}
                  className={`label-caps h-8 rounded-chip border px-2 ${on ? "border-signal text-signal" : "border-line text-muted hover:text-text"}`}
                >
                  {exName(ex)}
                </button>
              );
            })}
          </div>
          <select className={`${input} max-w-48`} value={f.sector} onChange={set("sector")} aria-label={t("cols.sector")}>
            <option value="">{t("allSectors")}</option>
            {sectors.map(([en, ar]) => (
              <option key={en} value={en}>
                {locale === "ar" ? (ar ?? en) : en}
              </option>
            ))}
          </select>
          <label className="flex flex-col gap-0.5"><span className="label-caps text-muted">{t("peMax")}</span><input className={numInput} inputMode="decimal" value={f.peMax} onChange={set("peMax")} /></label>
          <label className="flex flex-col gap-0.5"><span className="label-caps text-muted">{t("yieldMin")}</span><input className={numInput} inputMode="decimal" value={f.yieldMin} onChange={set("yieldMin")} /></label>
          <label className="flex flex-col gap-0.5"><span className="label-caps text-muted">{t("roeMin")}</span><input className={numInput} inputMode="decimal" value={f.roeMin} onChange={set("roeMin")} /></label>
          <label className="flex flex-col gap-0.5"><span className="label-caps text-muted">{t("r12Min")}</span><input className={numInput} inputMode="decimal" value={f.r12Min} onChange={set("r12Min")} /></label>
          <label className="flex flex-col gap-0.5"><span className="label-caps text-muted">{t("mcapMin")}</span><input className={numInput} inputMode="decimal" value={f.mcapMin} onChange={set("mcapMin")} /></label>
          <button type="button" onClick={() => setF(EMPTY)} className="h-8 px-2 text-muted hover:text-text">
            {t("reset")}
          </button>
          <span className="num ms-auto text-[12px] text-muted" data-screener-count={rows.length}>
            {t("count", { shown: rows.length, total: q.data?.length ?? 0 })}
          </span>
        </div>
        <div className="min-h-0 flex-1 overflow-auto">
          <QueryState isPending={q.isPending} error={q.error} rows={12} empty={!!q.data && rows.length === 0} emptyText={t("none")}>
            <table className="w-full min-w-[960px]">
              <thead className="sticky top-0 z-10 bg-panel">
                {table.getHeaderGroups().map((hg) => (
                  <tr key={hg.id}>
                    {hg.headers.map((h) => {
                      const sorted = h.column.getIsSorted();
                      const end = (h.column.columnDef.meta as { end?: boolean } | undefined)?.end;
                      return (
                        <th
                          key={h.id}
                          className={`label-caps cursor-pointer select-none px-2 py-2 font-normal text-muted hover:text-text ${end ? "text-end" : "text-start"}`}
                          onClick={h.column.getToggleSortingHandler()}
                          aria-sort={sorted === "asc" ? "ascending" : sorted === "desc" ? "descending" : "none"}
                        >
                          <table.FlexRender header={h} />
                          {sorted === "asc" ? " ↑" : sorted === "desc" ? " ↓" : ""}
                        </th>
                      );
                    })}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    tabIndex={0}
                    data-ticker-row={row.original.ticker.slug}
                    onClick={() => open(row.original.ticker)}
                    onKeyDown={(e) => e.key === "Enter" && open(row.original.ticker)}
                    className="cursor-pointer border-t border-line hover:bg-panel-raised focus-visible:bg-panel-raised"
                  >
                    {row.getAllCells().map((cell) => (
                      <td key={cell.id} className={`px-2 py-1.5 ${(cell.column.columnDef.meta as { end?: boolean } | undefined)?.end ? "text-end" : ""}`}>
                        <table.FlexRender cell={cell} />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </QueryState>
        </div>
      </Panel>
    </div>
  );
}
