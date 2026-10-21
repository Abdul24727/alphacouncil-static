// Dividend periods as the pipeline writes them, in the page's language (components/stock/research-panels.tsx).

const ORDINAL_AR: Record<string, string[]> = { Q: ["الأول", "الثاني", "الثالث", "الرابع"], H: ["الأول", "الثاني"] };

/**
 * A dividend's period as the database writes it ("Q 3 _ 2025", "H1-2026", "F Y _ 2025", "FY 2025") in
 * the page's language. Anything else in the note (a trailing "(…)", or a whole sentence) comes back
 * as `rest`, as stored: it is not translated.
 */
export function dividendPeriod(note: string | null | undefined, locale: string): { label: string | null; rest: string | null } {
  const raw = (note ?? "").trim();
  const m = raw.match(/^(?:([QH])\s*(\d)|F\s*Y)\s*[_-]?\s*(\d{4})\s*(?:\((.*)\))?$/i);
  if (!m) return { label: null, rest: raw || null };
  const [, kind, n, year, extra] = m;
  const k = kind?.toUpperCase();
  const label =
    locale === "ar"
      ? k
        ? `${k === "Q" ? "الربع" : "النصف"} ${ORDINAL_AR[k][Number(n) - 1] ?? n} ${year}`
        : `السنة المالية ${year}`
      : k
        ? `${k}${n} ${year}`
        : `FY ${year}`;
  return { label, rest: extra?.trim() || null };
}
