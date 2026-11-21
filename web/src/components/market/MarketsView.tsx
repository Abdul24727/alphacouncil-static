"use client";

import { useTranslations } from "next-intl";
import { Panel } from "@/components/panel/Panel";
import { QueryState, toTsv } from "@/components/stock/common";
import { useExchanges } from "@/lib/queries-app";
import { ExchangesTable } from "./HomeView";

/** The seven exchanges we cover, with a way into each one's equities. */
export function MarketsView() {
  const t = useTranslations("market");
  const q = useExchanges();
  const rows = q.data ?? [];

  return (
    <div className="@container min-h-0 flex-1 overflow-y-auto">
      <div className="grid grid-cols-12 gap-2.5 p-2.5">
        <Panel
          id="markets.exchanges"
          title={t("markets")}
          onRefresh={() => q.refetch()}
          copyData={() => toTsv(rows.map((e) => [e.exchange, e.equities, e.with_prices, e.index?.level, e.as_of]))}
          copilotData={() => rows}
          className="col-span-12"
        >
          <QueryState isPending={q.isPending} error={q.error} rows={7}>
            <p className="mb-2 text-text-soft">
              {t.rich("total", {
                n: (c) => <span className="num text-text">{c}</span>,
                equities: String(rows.reduce((n, e) => n + e.equities, 0)),
                exchanges: String(rows.length),
              })}
            </p>
            <ExchangesTable rows={rows} />
            {/* These were seven orange "Tadawul: 269 equities" links into the Screener. The count is
                the table's own total (with prices / equities) and the market names now link there. */}
            <p className="mt-3 text-[11.5px] text-muted">{t("browseNote")}</p>
          </QueryState>
        </Panel>
      </div>
    </div>
  );
}
