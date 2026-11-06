// Statement columns headed by the period the API says each one covers (components/stock/research-panels.tsx).
// A Saudi income statement is the last four quarters added together and a Saudi balance sheet can be a
// quarter-end position, so a column keyed "2026" is not a fiscal year 2026 (PROJECT.md, F-13).

export type StatementPeriod = {
  period: string | null; // FY | TTM | Q
  period_end: string | null; // "2026-06"
  aggregation?: string | null; // sum_quarters | quarter_end_snapshot | year_end_snapshot | …
  source_columns?: string[];
};

export type StatementColumn = {
  /** The key the row values use. */
  year: number;
  /** Short, for the column heading and the copied table. */
  heading: string;
  /** Says what the column is when it is not a fiscal year; shown under the table. */
  note: string | null;
};

const MONTHS_EN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTHS_AR = ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"];

/** "2026-06" as "Jun 2026" or "يونيو 2026"; null when it is not a year and month. */
export function monthYear(periodEnd: string | null | undefined, locale: string): string | null {
  const m = (periodEnd ?? "").match(/^(\d{4})-(\d{2})/);
  if (!m) return null;
  const month = Number(m[2]);
  if (month < 1 || month > 12) return null;
  return `${(locale === "ar" ? MONTHS_AR : MONTHS_EN)[month - 1]} ${m[1]}`;
}

function heading(year: number, p: StatementPeriod | undefined, aware: boolean, locale: string): Omit<StatementColumn, "year"> {
  const ar = locale === "ar";
  // The old response shape keyed values by fiscal year and said nothing else: keep its heading.
  if (!aware) return { heading: ar ? `${year}` : `FY${year}`, note: null };
  const end = monthYear(p?.period_end, locale);
  switch (p?.period) {
    case "FY":
      return { heading: ar ? `${year}` : `FY${year}`, note: null };
    case "TTM":
      if (!end) break;
      return ar
        ? {
            heading: `12 شهرًا حتى ${end}`,
            note: p.aggregation === "sum_quarters" ? `12 شهرًا حتى ${end}: مجموع الأرباع الأربعة المنتهية في ${end}.` : `12 شهرًا حتى ${end}: الاثنا عشر شهرًا المنتهية في ${end}.`,
          }
        : {
            heading: `TTM ${end}`,
            note: p.aggregation === "sum_quarters" ? `TTM ${end}: trailing twelve months, the four quarters to ${end} added together.` : `TTM ${end}: the twelve months to ${end}.`,
          };
    case "Q":
      if (!end) break;
      if (p.aggregation === "quarter_end_snapshot")
        return ar
          ? { heading: end, note: `${end}: المركز المالي في نهاية ذلك الربع، لا في نهاية سنة مالية.` }
          : { heading: end, note: `${end}: the position at that quarter-end, not a fiscal year-end.` };
      return ar
        ? { heading: `3 أشهر حتى ${end}`, note: `3 أشهر حتى ${end}: ربع واحد، الأشهر الثلاثة المنتهية في ${end}.` }
        : { heading: `3M ${end}`, note: `3M ${end}: one quarter, the three months to ${end}.` };
  }
  // A column the API could not date: claim no period for it.
  return ar
    ? { heading: `${year}`, note: `${year}: لا يحدد المصدر الفترة التي يغطيها هذا العمود.` }
    : { heading: `${year}`, note: `${year}: the source does not say which period this column covers.` };
}

/**
 * The columns one statement shows: the response's years that the statement dates or fills, each headed
 * by its own period. Years the statement has no figure and no period for are left out, so a trailing
 * income statement is not set beside an empty "FY2025".
 *
 * Newest first, as in Argaam's own grid: the newest period sits beside the line labels, so a phone,
 * which shows the labels and one or two columns before the table scrolls, opens on it, not on the
 * oldest year (2026-11-06).
 */
export function statementColumns(
  years: number[],
  periods: Record<string, StatementPeriod> | null | undefined,
  rows: { values: Record<string, number | null | undefined> }[],
  locale: string,
): StatementColumn[] {
  const aware = !!periods && Object.keys(periods).length > 0;
  const shown = years.filter((y) => (aware && periods![String(y)] != null) || rows.some((r) => r.values[String(y)] != null));
  return [...(shown.length ? shown : years)]
    .sort((a, b) => b - a)
    .map((year) => ({ year, ...heading(year, periods?.[String(year)], aware, locale) }));
}

/** The statement table's line-label column where the table scrolls (the panel's `min-w-48`, 12rem). */
export const STATEMENT_LABEL_PX = 192;

/** The width the table needs to show every column without scrolling (label, padding, ~96px a period). */
export const statementTableWidth = (columns: number) => Math.min(560, 208 + 96 * columns);

/**
 * Where a statement does not fit its box (a phone), the width of each period column: the box less the
 * line labels, so the box shows the labels and exactly one whole period, and scrolling (snapped to
 * columns) never leaves a figure cut in half beside the labels or at the edge (review 13, 2026-11-06).
 * Null where the table fits, which leaves the layout as it was. Never under 96px, a period's usual width.
 */
export function phoneColumnWidth(boxWidth: number, columns: number): number | null {
  if (!(boxWidth > 0) || columns < 1 || boxWidth >= statementTableWidth(columns)) return null;
  return Math.max(96, Math.floor(boxWidth - STATEMENT_LABEL_PX));
}
