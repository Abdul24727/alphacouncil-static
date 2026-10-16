import data from "@/content/data-labels.json";

// Statement lines, event names and capital-change types are stored in one language
// (Arabic for most tickers, English for some). Show each in the page's language when
// the dictionary knows it; otherwise as stored, tagged with its own language.
const norm = (s: string) => s.replace(/\s+/g, " ").trim().toLowerCase();
const isArabic = (s: string) => /[؀-ۿ]/.test(s);

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

export function dataLabel(text: string | null | undefined, locale: string): { text: string; lang: "en" | "ar" } {
  const raw = text ?? "";
  const n = norm(raw);
  if (locale === "ar") {
    if (isArabic(raw)) return { text: raw, lang: "ar" };
    const ar = toAr.get(n);
    return ar ? { text: ar, lang: "ar" } : { text: raw, lang: "en" };
  }
  if (!isArabic(raw)) return { text: canonical.get(n) ?? raw, lang: "en" };
  const en = toEn.get(n);
  return en ? { text: en, lang: "en" } : { text: raw, lang: "ar" };
}
