import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";
import { Suspense } from "react";
import { StockTemplate } from "@/components/stock/StockTemplate";
import { getTickerRef } from "@/lib/api/server";
import { localizedMetadata, titled } from "@/lib/seo";

/**
 * "Saudi Aramco (2222) · Tadawul" from the API's names and symbol (nothing else: no price in
 * the title or the preview). Every tab shares the canonical /t/<slug> of the API's slug, so
 * /t/2222_TADAWUL and /t/2222/financials consolidate on /t/2222.
 */
export async function generateMetadata({ params }: LayoutProps<"/[locale]/t/[ticker]">): Promise<Metadata> {
  const { locale, ticker } = await params;
  const slug = safeDecode(ticker);
  const [ref, t, tx] = await Promise.all([
    getTickerRef(slug),
    getTranslations({ locale, namespace: "meta" }),
    getTranslations({ locale, namespace: "exchanges" }),
  ]);
  const path = (s: string) => `/t/${encodeURIComponent(s)}`;
  if (ref === "unknown") return localizedMetadata(locale, path(slug), titled(t("stockUnknown")), undefined, true);
  // The API could not answer: a plain title, and no description it cannot back.
  if (!ref) return localizedMetadata(locale, path(slug), titled(slug));

  // Same fallback as the page header (TickerNames): the other language's name, then the symbol.
  const name = locale === "ar" ? (ref.name_ar ?? ref.name_en) : (ref.name_en ?? ref.name_ar);
  const company = name ? `${name} (${ref.symbol})` : ref.symbol;
  const exchange = tx.has(ref.exchange) ? tx(ref.exchange) : ref.exchange;
  return localizedMetadata(
    locale,
    path(ref.slug),
    titled(t("stockTitle", { company, exchange })),
    t("stockDescription", { company, exchange }),
  );
}

function safeDecode(s: string) {
  try {
    return decodeURIComponent(s);
  } catch {
    return s;
  }
}

// The ticker comes from the URL at request time, so the template streams in behind Suspense.
export default function Layout({ children, params }: LayoutProps<"/[locale]/t/[ticker]">) {
  return (
    <Suspense fallback={<div className="h-14 shrink-0 border-b border-line" />}>
      <StockLayout params={params}>{children}</StockLayout>
    </Suspense>
  );
}

/**
 * A ticker the universe does not have — a mistyped symbol, or a listing that stopped trading
 * (api/app/data/not_listed.json) — gets the not-found room instead of an empty stock shell, on
 * every tab. Only when the API says 404: an API that cannot answer returns null and the page
 * renders as usual, so an outage never turns every stock page into a not-found.
 *
 * The response is still HTTP 200 (a soft 404). With cacheComponents on, the route's shell is sent
 * before this runs, and Next cannot change a status code already on the wire; `export const instant
 * = false`, and moving this check into the layout body or into the page, were all tried and none of
 * them changed it. The page is marked noindex, so search engines drop these URLs either way, and
 * the owner settled on the soft 404 rather than pay for a real one in the proxy (PROJECT.md,
 * Decisions, 2026-10-24).
 */
async function StockLayout({
  params,
  children,
}: {
  params: LayoutProps<"/[locale]/t/[ticker]">["params"];
  children: React.ReactNode;
}) {
  const { ticker } = await params;
  const slug = decodeURIComponent(ticker);
  if ((await getTickerRef(slug)) === "unknown") notFound();
  return <StockTemplate slug={slug}>{children}</StockTemplate>;
}
