"use client";

import { SeatsPanel } from "./council";
import { CouncilPanel, MetricsPanel, NewsPanel, PeersPanel, PricePanel } from "./overview-panels";
import {
  CapitalPanel,
  DividendsPanel,
  EventsPanel,
  FundamentalsPanel,
  OwnershipPanel,
  SeasonalityPanel,
  StatementPanel,
} from "./research-panels";

// Fixed 12-column layouts per page (plan: no freeform grid). Breakpoints are
// container queries on the work area, not the window, because the sidebar and
// Copilot take a varying share of the screen. One column on phones.
const GRID = "grid grid-cols-12 gap-2.5 p-2.5";
const span = {
  full: "col-span-12",
  half: "col-span-12 @3xl:col-span-6",
  third: "col-span-12 @3xl:col-span-6 @6xl:col-span-4",
  wide: "col-span-12 @6xl:col-span-8",
  side: "col-span-12 @3xl:col-span-6 @6xl:col-span-4",
};

export function OverviewTab() {
  return (
    <div className={GRID}>
      <PricePanel className={`${span.wide} min-h-80`} />
      <MetricsPanel className={span.side} />
      <CouncilPanel className={span.third} />
      <PeersPanel className={span.third} />
      <NewsPanel className={span.third} />
    </div>
  );
}

export function FinancialsTab() {
  return (
    <div className={GRID}>
      <FundamentalsPanel className={span.full} />
      <StatementPanel section="Income Statement" className={span.full} />
      <StatementPanel section="Balance Sheet" className={span.full} />
    </div>
  );
}

export function CouncilTab() {
  return (
    <div className={GRID}>
      <CouncilPanel large className="col-span-12 @4xl:col-span-5" />
      <SeatsPanel className="col-span-12 @4xl:col-span-7" />
    </div>
  );
}

export function OwnershipTab() {
  return (
    <div className={GRID}>
      <OwnershipPanel className={span.full} />
    </div>
  );
}

export function CalendarTab() {
  return (
    <div className={GRID}>
      <EventsPanel className={span.half} />
      <DividendsPanel className={span.half} />
      <SeasonalityPanel className={span.wide} />
      <CapitalPanel className={span.side} />
    </div>
  );
}
