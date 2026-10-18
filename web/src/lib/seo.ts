import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";
import { routing, type Locale } from "@/i18n/routing";

/**
 * The one public address. Canonicals, hreflang alternates, Open Graph URLs and the sitemap
 * always point here, whichever host served the page (beta.alphacouncil.tech, a tunnel).
 */
export const SITE_URL = "https://alphacouncil.tech";
export const SITE_NAME = "AlphaCouncil";

/** Path of a page in a locale: English keeps the bare path, Arabic lives under /ar. */
export function localePath(locale: string, path: string): string {
  if (locale === routing.defaultLocale) return path;
  return path === "/" ? `/${locale}` : `/${locale}${path}`;
}

export const absoluteUrl = (locale: string, path: string) => `${SITE_URL}${localePath(locale, path)}`;

/** hreflang alternates of a path in every locale, English as x-default. */
export function languageAlternates(path: string): Record<string, string> {
  const out: Record<string, string> = {};
  for (const l of routing.locales) out[l] = absoluteUrl(l, path);
  out["x-default"] = absoluteUrl(routing.defaultLocale, path);
  return out;
}

const OG_LOCALE: Record<Locale, string> = { en: "en_US", ar: "ar_SA" };

/** Link-preview card (BRAND.md, no numbers): public/og/<locale>.png, made by scripts/capture-og.mjs. */
export const ogImage = (locale: string, alt: string) => ({
  url: `${SITE_URL}/og/${locale === "ar" ? "ar" : "en"}.png`,
  width: 1200,
  height: 630,
  alt,
  type: "image/png",
});

type PageMeta = {
  locale: string;
  /** Path without the locale prefix: "/", "/pricing", "/t/2222". */
  path: string;
  /** The whole <title>. */
  title: string;
  description?: string;
  /** Alt text of the preview card, in the page's language. */
  imageAlt: string;
  /** Keep out of search results (account pages, unknown tickers). */
  noindex?: boolean;
};

/**
 * Everything a public page needs in <head>: title and description in its language, canonical
 * on alphacouncil.tech, en/ar alternates, Open Graph and Twitter cards with the brand image.
 * Next replaces (does not merge) openGraph and twitter between segments, so each page sets all.
 */
export function pageMetadata({ locale, path, title, description, imageAlt, noindex }: PageMeta): Metadata {
  const url = absoluteUrl(locale, path);
  const image = ogImage(locale, imageAlt);
  const others = routing.locales.filter((l) => l !== locale).map((l) => OG_LOCALE[l]);
  return {
    title: { absolute: title },
    description,
    alternates: { canonical: url, languages: languageAlternates(path) },
    openGraph: {
      type: "website",
      siteName: SITE_NAME,
      url,
      title,
      description,
      locale: OG_LOCALE[locale as Locale] ?? OG_LOCALE.en,
      alternateLocale: others,
      images: [image],
    },
    twitter: { card: "summary_large_image", title, description, images: [image] },
    ...(noindex ? { robots: { index: false, follow: false } } : {}),
  };
}

/** "<page> · AlphaCouncil", the title of every page but the landing page. */
export const titled = (page: string) => (page.includes(SITE_NAME) ? page : `${page} · ${SITE_NAME}`);

/** pageMetadata for a page in a locale, with the preview card's alt text in that language. */
export async function localizedMetadata(
  locale: string,
  path: string,
  title: string,
  description?: string,
  noindex?: boolean,
): Promise<Metadata> {
  const t = await getTranslations({ locale, namespace: "meta" });
  return pageMetadata({ locale, path, title, description, imageAlt: t("ogAlt"), noindex });
}

/** Account pages: a title in the page's language, never indexed (robots.txt disallows them too). */
export async function privateMetadata(locale: string, page: string): Promise<Metadata> {
  const t = await getTranslations({ locale, namespace: "meta" });
  return { title: { absolute: titled(page) }, description: t("private"), robots: { index: false, follow: false } };
}
