import type { MetadataRoute } from "next";
import { isLegalDoc, LEGAL_DOCS, legalDocument } from "@/content/legal";
import { routing } from "@/i18n/routing";
import { getTickerList } from "@/lib/api/server";
import { absoluteUrl, languageAlternates } from "@/lib/seo";
import { TEMPLATES, templateHref } from "@/lib/templates";

// Public pages that need no account. The stock template opens at /t/<ticker>, listed below.
const PAGES = [
  "/",
  "/pricing",
  "/methodology",
  "/legal",
  ...LEGAL_DOCS.map((d) => `/legal/${d}`),
  "/home",
  "/markets",
  "/screener",
  "/templates",
  ...TEMPLATES.filter((n) => n !== "tadawul-stock").map(templateHref),
];

/** One entry per page and language, each with its en/ar alternates. */
function entries(path: string, lastModified?: (locale: string) => string | null | undefined): MetadataRoute.Sitemap {
  const languages = languageAlternates(path);
  return routing.locales.map((locale) => {
    const date = lastModified?.(locale);
    return { url: absoluteUrl(locale, path), ...(date ? { lastModified: date } : {}), alternates: { languages } };
  });
}

// A legal document is dated by its own "updated" (or "effective") line; other site pages carry
// no date in our data, so they have no lastmod.
const legalDate = (path: string) => (locale: string) => {
  const doc = path.split("/")[2];
  if (!doc || !isLegalDoc(doc)) return null;
  const d = legalDocument(locale, doc);
  return d.updated ?? d.effective;
};

/**
 * Every public page in English and Arabic, then every stock page from the API's ticker list,
 * dated by the last bar of its daily price file. Built per request (the list follows the
 * pipeline); if the API cannot answer, the site pages are still listed.
 */
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const tickers = await getTickerList();
  if (!tickers) console.error("sitemap: ticker list unavailable, stock pages left out");
  return [
    ...PAGES.flatMap((p) => entries(p, legalDate(p))),
    ...(tickers ?? []).flatMap((t) => entries(`/t/${encodeURIComponent(t.slug)}`, () => t.prices_as_of)),
  ];
}
