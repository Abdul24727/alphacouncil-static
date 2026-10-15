"use client";

import { CheckIcon, DrawingPinIcon } from "@radix-ui/react-icons";
import { useTranslations } from "next-intl";
import { priceDigits } from "@/components/stock/common";
import { PriceChart } from "@/components/stock/PriceChart";
import { useDashboards } from "@/lib/dashboards-store";
import { fmtNumber } from "@/lib/format";
import { useTickerPrices } from "@/lib/queries";
import { RichText } from "./RichText";
import type { ChartData, CopilotMessage, Sources, TableData } from "./types";

type Part = CopilotMessage["parts"][number];

// Stable reference so the inline chart is not rebuilt on every render.
const NO_INDICATORS: never[] = [];

function isTool(p: Part): p is Extract<Part, { toolCallId: string }> {
  return p.type === "dynamic-tool" || p.type.startsWith("tool-");
}

function toolName(p: Extract<Part, { toolCallId: string }>) {
  return "toolName" in p && typeof p.toolName === "string" ? p.toolName : p.type.replace(/^tool-/, "");
}

function tickerOf(p: Extract<Part, { toolCallId: string }>): string | null {
  const input = "input" in p ? (p.input as Record<string, unknown> | undefined) : undefined;
  return input && typeof input.ticker === "string" ? input.ticker : null;
}

export function UserMessage({ message }: { message: CopilotMessage }) {
  const text = message.parts.map((p) => (p.type === "text" ? p.text : "")).join("");
  return (
    <div className="ms-8 self-end rounded-panel bg-panel-raised px-3 py-2 text-text" dir="auto">
      {text}
    </div>
  );
}

export function AssistantMessage({
  message,
  streaming,
  onFollowUp,
}: {
  message: CopilotMessage;
  streaming: boolean;
  onFollowUp: (q: string) => void;
}) {
  const t = useTranslations("copilot");
  const parts = message.parts;
  const sources: Sources = (parts.find((p) => p.type === "data-sources") as { data: Sources } | undefined)?.data ?? {};
  const steps = parts.filter((p) => p.type === "reasoning" || isTool(p));
  const text = parts
    .map((p) => (p.type === "text" ? p.text : ""))
    .join("")
    .trim();
  const tables = parts.flatMap((p) => (p.type === "data-table" ? [p.data as TableData] : []));
  const charts = parts.flatMap((p) => (p.type === "data-chart" ? [p.data as ChartData] : []));
  const followUps = parts.flatMap((p) => (p.type === "data-followups" ? (p.data as { questions: string[] }).questions : []));

  return (
    <div className="flex flex-col gap-2" data-message="assistant">
      {steps.length > 0 && (
        <details className="group rounded-panel border border-line">
          <summary className="label-caps flex cursor-pointer list-none items-center gap-2 px-2 py-1.5 text-muted hover:text-text">
            <span className="transition-transform group-open:rotate-90 rtl:-scale-x-100">›</span>
            {t("reasoning", { n: steps.length })}
            {streaming && !text && <span className="ms-auto animate-pulse normal-case tracking-normal">{t("thinking")}…</span>}
          </summary>
          <ol className="flex flex-col gap-1.5 border-t border-line px-2 py-2 text-[12px]">
            {steps.map((p, i) =>
              p.type === "reasoning" ? (
                <li key={i} className="whitespace-pre-wrap text-muted" dir="auto">
                  {p.text}
                </li>
              ) : isTool(p) ? (
                <li key={i} className="flex items-center gap-2 text-text-soft">
                  <span className={p.state === "output-available" ? "text-gain" : "text-muted"}>
                    {p.state === "output-available" ? <CheckIcon /> : "·"}
                  </span>
                  <span>{t.has(`tools.${toolName(p)}`) ? t(`tools.${toolName(p)}`) : toolName(p)}</span>
                  {tickerOf(p) && <span className="num text-[11px] text-muted">{tickerOf(p)}</span>}
                </li>
              ) : null,
            )}
          </ol>
        </details>
      )}

      {text && <RichText text={text} sources={sources} />}
      {!text && streaming && steps.length === 0 && <span className="animate-pulse text-muted">{t("thinking")}…</span>}

      {tables.map((tb) => (
        <CopilotTable key={tb.id} table={tb} />
      ))}
      {charts.map((c) => (
        <CopilotChart key={c.id} chart={c} />
      ))}

      {followUps.length > 0 && !streaming && (
        <div className="flex flex-col items-start gap-1" aria-label={t("followUps")}>
          {followUps.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => onFollowUp(q)}
              dir="auto"
              className="rounded-chip border border-line px-2 py-1 text-start text-text-soft hover:border-signal/50 hover:text-text"
            >
              {q}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function PinButton({ pinned, onPin }: { pinned: boolean; onPin: () => void }) {
  const t = useTranslations("copilot");
  return (
    <button
      type="button"
      onClick={onPin}
      disabled={pinned}
      className={`flex items-center gap-1 rounded-chip px-1.5 py-0.5 text-[11px] ${pinned ? "text-gain" : "text-muted hover:text-signal"}`}
    >
      {pinned ? <CheckIcon /> : <DrawingPinIcon />}
      {pinned ? t("pinned") : t("pin")}
    </button>
  );
}

export function CopilotTable({ table }: { table: TableData }) {
  const t = useTranslations("copilot");
  const pinned = useDashboards((s) => s.pinned.some((p) => p.id === table.id));
  const pin = useDashboards((s) => s.pin);
  const flagged = new Set(table.unverified.map(([r, c]) => `${r}:${c}`));

  return (
    <figure className="overflow-hidden rounded-panel border border-line" data-copilot-table={table.id}>
      <figcaption className="flex items-center gap-2 border-b border-line px-2 py-1">
        <span className="min-w-0 flex-1 truncate text-text" dir="auto">
          {table.title}
        </span>
        <span className="label-caps text-muted">{table.source}</span>
        <PinButton
          pinned={pinned}
          onPin={() => pin({ kind: "table", ...table, pinnedAt: new Date().toISOString() })}
        />
      </figcaption>
      <div className="overflow-x-auto">
        <DataTable table={table} flagged={flagged} unverifiedLabel={t("unverified")} />
      </div>
    </figure>
  );
}

export function DataTable({
  table,
  flagged,
  unverifiedLabel,
}: {
  table: Pick<TableData, "columns" | "rows">;
  flagged: Set<string>;
  unverifiedLabel: string;
}) {
  return (
    <table className="w-full text-[12px]">
      <thead>
        <tr className="label-caps text-muted">
          {table.columns.map((c) => (
            <th key={c} className="px-2 py-1 text-start font-normal" dir="auto">
              {c}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {table.rows.map((row, r) => (
          <tr key={r} className="border-t border-line">
            {row.map((cell, c) => {
              const bad = flagged.has(`${r}:${c}`);
              const isNum = typeof cell === "number";
              return (
                <td
                  key={c}
                  title={bad ? unverifiedLabel : undefined}
                  className={`px-2 py-1 ${isNum ? "num text-end" : ""} ${bad ? "text-stale underline decoration-dotted" : "text-text"}`}
                  dir={isNum ? "ltr" : "auto"}
                >
                  {cell == null ? "—" : isNum ? (fmtNumber(cell, Math.abs(cell) >= 100 ? 0 : cell % 1 ? 2 : 0) ?? String(cell)) : cell}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function CopilotChart({ chart }: { chart: ChartData }) {
  const prices = useTickerPrices(chart.ticker);
  const pinned = useDashboards((s) => s.pinned.some((p) => p.id === chart.id));
  const pin = useDashboards((s) => s.pin);
  const p = prices.data;
  if (!p?.has_history) return null;

  return (
    <figure className="overflow-hidden rounded-panel border border-line" data-copilot-chart={chart.id}>
      <figcaption className="flex items-center gap-2 border-b border-line px-2 py-1">
        <span className="num flex-1 text-text">
          {chart.ticker} · {chart.range}
        </span>
        <PinButton
          pinned={pinned}
          onPin={() =>
            pin({ kind: "chart", id: chart.id, title: `${chart.ticker} · ${chart.range}`, ticker: chart.ticker, range: chart.range, pinnedAt: new Date().toISOString() })
          }
        />
      </figcaption>
      <PriceChart bars={p.bars} mode="line" range={chart.range} indicators={NO_INDICATORS} digits={priceDigits(p.currency)} height={170} />
    </figure>
  );
}
