import type { MetadataRoute } from "next";
import { routing } from "@/i18n/routing";
import { localePath, SITE_URL } from "@/lib/seo";

// Account pages: nothing on them is public. /billing/ covers /billing/return.
const PRIVATE = ["/portfolio", "/settings", "/dashboards", "/checkout", "/billing/", "/verify-email", "/reset-password"];

/**
 * The same file on every host: beta.alphacouncil.tech is kept out of search engines by its
 * password and the X-Robots-Tag nginx sends there (deploy/nginx-beta.conf).
 */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/", ...routing.locales.flatMap((l) => PRIVATE.map((p) => localePath(l, p)))],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
