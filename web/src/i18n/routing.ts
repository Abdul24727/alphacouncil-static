import { defineRouting } from "next-intl/routing";

// English keeps the plan's paths (/home, /t/2222); Arabic lives under /ar.
export const routing = defineRouting({
  locales: ["en", "ar"],
  defaultLocale: "en",
  localePrefix: "as-needed",
  // hreflang comes from each page's metadata (lib/seo.ts), on alphacouncil.tech and the canonical
  // slug; the middleware's Link header would repeat it from whatever URL and host was requested.
  alternateLinks: false,
});

export type Locale = (typeof routing.locales)[number];

export function dirFor(locale: Locale): "ltr" | "rtl" {
  return locale === "ar" ? "rtl" : "ltr";
}
