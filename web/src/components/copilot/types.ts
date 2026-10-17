import type { UIMessage } from "ai";
import type { ChartRange } from "@/components/stock/PriceChart";

export type TableData = {
  id: string;
  title: string;
  columns: string[];
  rows: (string | number | null)[][];
  source: string;
  /** [row, col] of numeric cells not found in the data the Copilot read. */
  unverified: number[][];
};

export type ChartData = { id: string; ticker: string; ticker_key?: string; range: ChartRange };

/** Citation tag -> panel (P1, P2 ...) or the database (DB). */
export type Sources = Record<string, { id: string | null; title: string; ticker: string | null }>;

export type CopilotMessage = UIMessage<
  never,
  {
    table: TableData;
    chart: ChartData;
    followups: { questions: string[] };
    model: { name: string; stand_in: boolean };
    sources: Sources;
    autocite: { sentence: string; tags: string[] }[];
  }
>;
