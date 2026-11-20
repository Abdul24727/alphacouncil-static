import createMiddleware from "next-intl/middleware";
import type { NextRequest } from "next/server";
import { routing } from "./i18n/routing";

// The URL decides the language (design fix 6, owner 2026-11-21): /pricing is English and
// /ar/pricing is Arabic, whatever the remembered-locale cookie or the browser says. Only the
// bare "/" still looks at them (cookie, then Accept-Language) to pick English or /ar.
// Both handlers keep the cookie in step with the language of the page opened.
const fromUrl = createMiddleware({ ...routing, localeDetection: false });
const detecting = createMiddleware(routing);

export default function proxy(request: NextRequest) {
  return request.nextUrl.pathname === "/" ? detecting(request) : fromUrl(request);
}

export const config = {
  // Skip the API proxy, Next internals and static files. Only real file extensions are
  // excluded: ticker slugs such as /t/ADAV.AD or /t/NBB.BH contain dots.
  matcher: "/((?!api|_next|_vercel|.*\\.(?:ico|png|jpe?g|gif|svg|webp|avif|woff2?|ttf|txt|xml|json|map|js|css|webmanifest)$).*)",
};
