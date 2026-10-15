"use client";

import { useTranslations } from "next-intl";
import { useEffect } from "react";
import { DataTable } from "@/components/copilot/Message";
import { Panel, PanelUnavailable } from "@/components/panel/Panel";
import { priceDigits, toTsv } from "@/components/stock/common";
import { PriceChart } from "@/components/stock/PriceChart";
import { type PinnedChart, type PinnedTable, useDashboards } from "@/lib/dashboards-store";
import { fmtStamp } from "@/lib/format";
import { useTickerPrices } from "@/lib/queries";

const NO_INDICATORS: never[] = [];

/** My dashboards: Copilot answers pinned as panels (browser-local until accounts exist). */
export function DashboardsView() {
  const t = useTranslations("dashboards");
  const pinned = useDashboards((s) => s.pinned);
  useEffect(() => {
    void useDashboards.persist.rehydrate();
  }, []);

  if (pinned.length === 0) {
    return (
      <div className="p-2.5">
        <Panel id="dashboards.empty" title={t("title")}>
          <PanelUnavailable detail={t("empty")} />
        </Panel>
      </div>
    );
  }
  return (
    <div className="@container min-h-0 flex-1 overflow-y-auto">
      <div className="grid grid-cols-12 gap-2.5 p-2.5">
        {pinned.map((p) =>
          p.kind === "table" ? (
            <PinnedTablePanel key={p.id} item={p} />
          ) : (
            <PinnedChartPanel key={p.id} item={p} />
          ),
        )}
      </div>
    </div>
  );
}

function useUnpin(id: string) {
  const t = useTranslations("dashboards");
  const unpin = useDashboards((s) => s.unpin);
  return [{ key: "unpin", label: t("unpin"), onSelect: () => unpin(id) }];
}

function PinnedTablePanel({ item }: { item: PinnedTable }) {
  const t = useTranslations("dashboards");
  const tc = useTranslations("copilot");
  const menu = useUnpin(item.id);
  return (
    <Panel
      id={`pinned.${item.id}`}
      title={item.title}
      copyData={() => toTsv([item.columns, ...item.rows])}
      copilotData={() => ({ columns: item.columns, rows: item.rows, source: item.source, pinnedAt: item.pinnedAt })}
      menuItems={menu}
      className="col-span-12 @4xl:col-span-6"
      bodyClassName="p-0"
    >
      <p className="label-caps px-3 pt-2 text-muted">
        {t("pinnedAt", { when: fmtStamp(item.pinnedAt) ?? "" })} · {item.source}
      </p>
      <div className="overflow-x-auto p-1">
        <DataTable table={item} flagged={new Set(item.unverified.map(([r, c]) => `${r}:${c}`))} unverifiedLabel={tc("unverified")} />
      </div>
    </Panel>
  );
}

function PinnedChartPanel({ item }: { item: PinnedChart }) {
  const menu = useUnpin(item.id);
  const prices = useTickerPrices(item.ticker);
  const p = prices.data;
  return (
    <Panel
      id={`pinned.${item.id}`}
      title={item.title}
      ticker={item.ticker}
      freshness={p ? p.freshness : undefined}
      onRefresh={() => prices.refetch()}
      copilotData={() => ({ ticker: item.ticker, range: item.range, last: p?.bars.at(-1) })}
      menuItems={menu}
      className="col-span-12 @4xl:col-span-6"
      bodyClassName="p-1"
    >
      {p?.has_history ? (
        <PriceChart bars={p.bars} mode="line" range={item.range} indicators={NO_INDICATORS} digits={priceDigits(p.currency)} height={260} />
      ) : (
        <PanelUnavailable />
      )}
    </Panel>
  );
}
