// The label lookup behind lib/data-labels.ts, with no imports so tests can run it on the real dictionary
// (node --test does not resolve the "@/" alias).
//
// Statement lines, event names and capital-change types are stored in one language (Arabic for most
// tickers, English for some). Show each in the page's language when the dictionary knows it; otherwise as
// stored, tagged with its own language. A few statement lines mean something else inside one statement
// (`in_statement`): given that statement, they are shown with that meaning in both languages.

export type LabelData = {
  pairs: string[][];
  aliases: Record<string, string>;
  in_statement?: Record<string, { match: string[]; en: string; ar: string }[]>;
};
export type DataLabel = { text: string; lang: "en" | "ar" };

const norm = (s: string) => s.replace(/\s+/g, " ").trim().toLowerCase();
const isArabic = (s: string) => /[؀-ۿ]/.test(s);

export function makeDataLabel(data: LabelData) {
  const toAr = new Map<string, string>();
  const toEn = new Map<string, string>();
  for (const [en, ar] of data.pairs) {
    if (!toAr.has(norm(en))) toAr.set(norm(en), ar);
    if (!toEn.has(norm(ar))) toEn.set(norm(ar), en);
  }
  // Raw database spellings ("Right IssueCancelled", "cash dividend distribution").
  const canonical = new Map<string, string>();
  for (const [raw, en] of Object.entries(data.aliases)) {
    canonical.set(norm(raw), en);
    const ar = toAr.get(norm(en));
    if (ar && !toAr.has(norm(raw))) toAr.set(norm(raw), ar);
  }
  // statement -> stored text (either language) -> { en, ar }
  const inStatement = new Map<string, Map<string, { en: string; ar: string }>>();
  for (const [statement, entries] of Object.entries(data.in_statement ?? {})) {
    const m = new Map<string, { en: string; ar: string }>();
    for (const e of entries) for (const t of e.match) m.set(norm(t), { en: e.en, ar: e.ar });
    inStatement.set(statement, m);
  }

  return function dataLabel(text: string | null | undefined, locale: string, statement?: string): DataLabel {
    const raw = text ?? "";
    const n = norm(raw);
    const own = statement ? inStatement.get(statement)?.get(n) : undefined;
    if (own) return locale === "ar" ? { text: own.ar, lang: "ar" } : { text: own.en, lang: "en" };
    if (locale === "ar") {
      if (isArabic(raw)) return { text: raw, lang: "ar" };
      const ar = toAr.get(n);
      return ar ? { text: ar, lang: "ar" } : { text: raw, lang: "en" };
    }
    if (!isArabic(raw)) return { text: canonical.get(n) ?? raw, lang: "en" };
    const en = toEn.get(n);
    return en ? { text: en, lang: "en" } : { text: raw, lang: "ar" };
  };
}
