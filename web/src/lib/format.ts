/**
 * Number and time formatting. Numbers always use Latin digits and stay
 * left-to-right (BRAND.md / Phase 7), whatever the UI language.
 */

const nf = (opts: Intl.NumberFormatOptions) => new Intl.NumberFormat("en-US", opts);

export function fmtNumber(v: number | null | undefined, digits = 2): string | null {
  if (v == null || !Number.isFinite(v)) return null;
  return nf({ minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v);
}

export function fmtInt(v: number | null | undefined): string | null {
  if (v == null || !Number.isFinite(v)) return null;
  return nf({ maximumFractionDigits: 0 }).format(v);
}

/** 1234567 -> "1.23M"; 6413000 (millions) with unit "M" -> "6.41T". */
export function fmtCompact(v: number | null | undefined, digits = 2): string | null {
  if (v == null || !Number.isFinite(v)) return null;
  return nf({ notation: "compact", maximumFractionDigits: digits }).format(v);
}

/** Percent where the value is already in percent units (5.03 -> "5.03%"). */
export function fmtPct(v: number | null | undefined, digits = 2, signed = false): string | null {
  if (v == null || !Number.isFinite(v)) return null;
  const s = nf({ minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v);
  return `${signed && v > 0 ? "+" : ""}${s}%`;
}

/** Percent where the value is a ratio (0.104 -> "10.4%"). */
export function fmtRatioPct(v: number | null | undefined, digits = 1, signed = false): string | null {
  return v == null ? null : fmtPct(v * 100, digits, signed);
}

export function signClass(v: number | null | undefined): string {
  if (v == null || v === 0) return "text-text";
  return v > 0 ? "text-gain" : "text-loss";
}

const sameDay = (a: Date, b: Date) =>
  a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();

/** "14:05" today, otherwise "12 Aug 14:05" (or "12 Aug 2025 14:05" in another year). */
export function fmtStamp(iso: string | null | undefined, now = new Date()): string | null {
  if (!iso) return null;
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return null;
  const time = d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
  if (sameDay(d, now)) return time;
  const date = d.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    ...(d.getFullYear() !== now.getFullYear() ? { year: "numeric" } : {}),
  });
  return `${date} ${time}`;
}

/** "12 Aug 2026" for date-only values such as a trading day. */
export function fmtDate(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const d = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
  if (Number.isNaN(d.getTime())) return null;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}
