"use client";

import { useTranslations } from "next-intl";
import { Panel } from "@/components/panel/Panel";
import { QueryState, toTsv } from "@/components/stock/common";
import { Link } from "@/i18n/navigation";
import { useExchanges } from "@/lib/queries-app";
import { ExchangesTable } from "./HomeView";
import { useExchangeName } from "./shared";

/** The seven exchanges we cover, with a way into each one's equities. */
export function MarketsView() {
  const t = useTranslations("market");
  const name = useExchangeName();
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
            <p className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
              {rows.map((e) => (
                <Link key={e.exchange} href={`/screener?exchange=${e.exchange}`} className="text-signal hover:underline">
                  {t("browse", { exchange: name(e.exchange), n: e.equities })}
                </Link>
              ))}
            </p>
          </QueryState>
        </Panel>
      </div>
    </div>
  );
}
